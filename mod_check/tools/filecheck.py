'''
@summary: Search model files and check all files exist.

@author: Duncan R.
@organization: Ermeview Environmental Ltd
@created 23rd March 2021
@copyright: Ermeview Environmental Ltd
@license: LGPL v2

Credit to Matthew Shallcross who wrote the majority of this functionality.
'''

import os
import sys
import csv
from pprint import pprint


class FileChecker():
    
    def __init__(self):
        super().__init__()
        
        
    def auditModelFiles(self, model_root):
        write_results = False
        filelog = os.path.join(model_root, 'mat_log.txt')
        searchlog = os.path.join(model_root, 'mat_search.txt')

        errors = {}
        error_count = 0
        search_successes = 0

        with open(filelog, 'w') as log_out, open(searchlog, 'w') as search_out:
            #model_root = "C:\\tmac\\_utils\\mat\\testmodel2"
            #model_root = "P:\\00 Project Files\\13037 River Brent Central London Model Pell Frischmann\\Received\\130626 Model Files (Pell Frischmann)\\Files\\Brent_model_zip\\Brent_v04.9-A&B_ModelFiles\\T Drive\\Brent_EVY0198"
            
            if write_results:
                log_out.write("M.A.T - TMac Model Audit Tool\nModel Files and Path Audit Results\n\n")
                search_out.write("M.A.T - TMac Model Audit Tool\nPath Errors and Search Results\n\n")
            
            audit = AuditFiles(model_root)
            audit.categorise()
            result_holder = ResultHolder()
            result_holder.summary = audit.getSummary()
            
            if write_results:
                log_out.write(audit.summary())
            
#             logger.info(audit.summary())
    #         print audit.summary()
            
            for f in audit.getModelFiles():
                errorlist = []
                if write_results:
                    log_out.write(f.getFilePath() + '\n')
                
                fpath = f.getFilePath()
                if fpath in result_holder.seen_parents: continue

                result_holder.parent = fpath
                result_holder.seen_parents.append(fpath)
                
                for p, line in f.getPathsToCheck():
                    if not p.isReal():
                        
                        path_as_read = p.getPathAsRead()
                        result_holder.addMissing(p.pathAsRead, line)
                        
                        error_count += 1
                        errorlist.append((p, line))
                        if write_results:
                            search_out.write("Model file " + f.getFilePath() + " has an error on line " + str(line) + '\n')
                        search_result = p.find(audit)
                        if len(search_result) > 0:
                            
                            try:
                                result_holder.setFound(p.pathAsRead, search_result)
                            except KeyError:
                                pass
#                                 logger.warning('Path key does not exist')
                            
                            if write_results:
                                search_out.write("File found here: " + search_result + '\n\n')
                            search_successes += 1
                        else:
                            if write_results:
                                search_out.write(p.getPathFileName() + " can not be found or incomplete GIS." + '\n\n')
                    
                    
                    if write_results:
                        log_out.write('< ' + str(line) + ' >\t' + p.getPathAsRead() + ' ' + str(p.isReal()) + '\n')
                errors[f] = errorlist
                
            if write_results:
                search_out.write("Total path errors:  " + str(error_count))
                search_out.write("\nFile search successes:  " + str(search_successes))

#             logger.info('Done')
            return result_holder
        

class Audit(object):
    '''
        Parent class for all of the audit tools
    '''
    def __init__(self, model_root):
        self.model_root = model_root
        #print 'initialised audit'
        if not os.path.isdir(model_root):
            raise ValueError ('Unable to find that directory')


class ResultHolder(object):    
    """
    """
    
    def __init__(self):
        self.parent = ''
        self.seen_parents = []
        self.missing = {}
        self.summary = {}
#         self.found = {}
    
    def addMissing(self, path, line, found=''):
        if path in self.missing:
            if not self.parent in self.missing[path]['parent']:
                self.missing[path]['parent'].append(self.parent)
                self.missing[path]['line'].append(line)
        else:
            self.missing[path] = {'parent': [self.parent], 'line': [line], 'found': found}
    
    def setFound(self, path, found):
        try:
            self.missing[path]['found'] = found
        except KeyError:
            raise 


class AuditFiles(Audit):
    '''
        Path checking audit tool
    '''
    def __init__(self, model_root):
        '''
            Takes a string describing the path to the root of the model folder structure being audited
        '''
        Audit.__init__(self, model_root)
        #print 'initialised auditpaths'        
        self.modelFiles = []
        self.otherFiles = []
        self.ignoreFiles = []
#         self.categorise()
                

    def categorise(self):
        '''
            Method for categorising the model passed to the audit tool
            Return: tuple contain list of ModelFile and list of SomeFile instances
        '''
        try:
#             print "Walking folder structure..."
#             logger.info('Walking folder structure...')
            # walk the model folder structure categorising ignore, model and other (eg GIS, csv) files
            for root, dirs, files in os.walk(self.model_root):
                
                for f in files:
                    filepath = os.path.join(root,f)
                    query = SomeFile(filepath)
                    if query.isIgnoreFile():
                        self.ignoreFiles.append(query)
                    # model files each have there own class describing their expected format
                    elif query.isModelFile():
                        self.modelFiles.append(model_file_exts[query.getFileExt()](filepath))

                    else:
                        self.otherFiles.append(query)

            #print 'model files\n', self.modelFiles
            #print 'other files\n', otherFiles
            #print "~AuditFiles.categorise~"
        except Exception as err:
#             logger.error('Could not traverse the model structure')
#             print 'Could not traverse the model structure'
#             logger.exception(err)
            raise
            
#     def listFiles(self):
#         '''
#             Method for listing the categorised files in the model folder
#         '''
# #         print '\nFound model files:'
# #         logger.info('\nFound model files:')
#         
#         for s in self.modelFiles:
# #             print ' ' + s.getName()
# #             logger.info(' ' + s.getName)
#             
# #         print '\nFound other files:'
# #         logger.info('\nFound other files:')
#         
#         for s in self.otherFiles:
# #             print ' ' + s.getName()
# #             logger.info(' ' + s.getName())
#         
# #         print '\nIgnored files:'
# #         logger.info('\nIgnored files:')
#         
#         for s in self.ignoreFiles:
# #             print ' ' + s.getName()
# #             logger.info(' ' + s.getName())
            
    def getModelFiles(self):
        return self.modelFiles
        
    def getOtherFiles(self):
        return self.otherFiles
    
    def getSummary(self):    
        """"""
        return {
            'model_files': str(len(self.modelFiles)),
            'other_files': str(len(self.otherFiles)),
            'ignored_files': str(len(self.ignoreFiles)),
            'total_files': str(len(self.ignoreFiles) + len(self.otherFiles) + len(self.ignoreFiles))
        }
        
    def summary(self):
        '''
            Method for printing a summary of the file structure of the model
        
        print "Model files:  \t" + str(len(self.modelFiles))
        print "Other files:  \t" + str(len(self.otherFiles))
        print "Ignored files:\t" + str(len(self.ignoreFiles))
        print "Total         \t" + str(len(self.modelFiles)+len(self.otherFiles)+len(self.ignoreFiles))
        '''
        return "\nModel files:  \t" + str(len(self.modelFiles)) + "\nOther files:  \t" + str(len(self.otherFiles))+"\nIgnored files:\t" + str(len(self.ignoreFiles)) + "\nTotal         \t" + str(len(self.modelFiles) + len(self.otherFiles) + len(self.ignoreFiles)) + '\n'

        
class SomeFile(object):
    '''
        Class for any file found in the model structure
    '''
    def __init__(self, filepath):
        self.filepath = filepath
        # basepath and file name
        self.path, self.name = os.path.split(filepath)
        # File extension (converted to lower case)
        self.fileExt = self.name.rsplit('.',1)[-1].lower()
        # Test to see if file extension is specified as a model file
        self.modelFile = self.fileExt in model_file_exts.keys()
        # Test to see if it's a file extension we can ignore
        self.ignoreFile = self.fileExt in ignore_file_exts
        
    def getFilePath(self):
        return self.filepath
        
    def getPath(self):
        return self.path
        
    def getName(self):
        return self.name
        
    def getFileExt(self):
        return self.fileExt
        
    def isModelFile(self):
        return self.modelFile
        
    def isIgnoreFile(self):
        return self.ignoreFile
        
        
class ModelFile(SomeFile):
    '''
        Class for model files found in the model structure
    '''
    def __init__(self, filepath):
        SomeFile.__init__(self, filepath)
        self.filepath = filepath
        self.path, self.name = os.path.split(filepath)
        self.pathsToCheck = self.PathSearch()
        
    def isModelFile(self):
        return True
        
    def PathSearch(self, terms, comment = '\n', splitOn = None, inactiveLines = False):
        '''
            Find lines containing each search variable in list 'terms' (a list of strings)
            Optional 'comment' string ignores text that appears after that string in a line
            !!!    NOT CURRENTLY USED: Optional inactiveLines switch allows you to search lines that have been commented-out at the beginning of the line
            Returns a list of the active lines containing the search terms (after removing comments)
        '''
        def ExtractPath(line, splitOn):
            '''
                Helper function to extract the paths found in the active lines containing the search term
                It simply right splits on the 'splitOn' string
            '''
            return line.rsplit(splitOn,1)[-1].strip()
            
            
        def TermSearch(term, text):
            '''
                Helper function to check 'term' is a string and that it is in 'text'
            '''
            if type(term) != type(''):
                raise TypeError ('Search term must be a string')
            return term in text
            

        def checkForPipes(line):
            """Checks the line to see if it contains multiple files.
            
            Some commands in tuflow can contain multiple files seperate by a pipe
            "|" charactar. This checks to see if that's the case and returns the
            file names if so.
            Sometimes pipe commands can be values to adjust parameters with, such
            as the materials file manning's adjustment. This checks whether the
            value is an int or a float, if not it's added.
            """
            # Break line
            #
            line = line.strip()
            command, instruction = line.split('==', 1)
            command = command.strip()
            instruction = instruction.strip()
            
            # check for pipes
            #
            found, split, comment_char = separateComment(instruction)
            instruction = split[0].strip()

            instructions = instruction.split('|')
            out = []
            if len(instructions) > 1:
                for i in instructions:
                    # Make sure it's not an adjustment value
                    i = i.strip()
                    try:
                        temp = int(i)
                    except ValueError:
                        try:
                            temp = float(i)
                        except ValueError:
                            out.append([command + ' == ' + i.strip(), i.strip()])
            else:
                out.append([line, instructions[0]])
            
            return out
        

        def separateComment(line):
            """Separates any comment from the line.
            """
            comment_char = None
            if '!' in line:
                comment_char = '!'

            if '#' in line:
                comment_char = '#'

            if not comment_char is None:
                split = line.split(comment_char, 1)
            else:
                split = [line]
                comment_char = ''
        
            if len(split) > 1:
                return True, split, comment_char
            else:
                return False, split, comment_char
        

        results = []
        
        with open(self.filepath, 'r') as mf:
            for lineNum, lineText in enumerate(mf,1):
                #print lineNum, lineText,
                lineText = lineText.rstrip()
                # ignore blank lines
                if lineText == '':
                    continue
                # remove text that follows the 'comment' string    
                activeText = lineText.split(comment,1)[0]
                # print lineNum, activeText
                # store the paths in lines that contain our search terms as ModelPath instances
                for i, term in enumerate(terms):
                    try:
                        if TermSearch(term, activeText): 
                            # Separate any piped file command if found
                            if '==' in activeText and splitOn == '==':
                                paths = checkForPipes(activeText)
                                for p in paths:
#                                     results.append(((ModelPath(ExtractPath(activeText, splitOn), self.path)), lineNum))
                                    results.append(((ModelPath(p[0], p[1], self.path)), lineNum))
                            else:
                                splitText = ExtractPath(activeText, splitOn)
                                results.append(((ModelPath(splitText, splitText, self.path)), lineNum))
                            break
                    except TypeError:
                        pass
#                         logger.warning('Search term [' + str(i) + '] is not a string and has been ignored')
#                         print 'Search term [' + str(i) + '] is not a string and has been ignored'
        
        #print "~ModelFile.PathSearch~"
        return results
        
    def getPathsToCheck(self):
        return self.pathsToCheck            
                        

class ModelPath():
    '''
        Class for path data and methods extracted from model files
    '''
    def __init__(self, extractedPath, pathAsRead, pathOfContainingFile):
        self.pathAsRead = pathAsRead
        self.pathOfContainingFile = pathOfContainingFile        
        self.pathFileName = os.path.basename(extractedPath)
        self.pathFileExt = self.pathFileName.rsplit('.',1)[-1].lower()
        
        # check if absolute and set absPath string accordingly
        if not os.path.isabs(extractedPath):
            self.absPath = os.path.normpath(os.path.join(self.pathOfContainingFile, self.pathAsRead))
        else:
            self.absPath = extractedPath
        
        self.real = self.check()
        
    def getPathFileName(self):
        return self.pathFileName
        
    def getPathFileExt(self):
        return self.pathFileExt
                        
    def getPathAsRead(self):
        return self.pathAsRead
        
    def getPathOfContainingFile(self):
        return self.pathOfContainingFile
    
    def getAbsPath(self):
        return self.absPath
        
    def check(self):
        '''
            Returns true if path exists, false otherwise
        '''
        # if we are looking for a mid file we need a mif file (and vice versa).
        
        #print "~ModelPath.check~"
        
        if self.getPathFileExt() == 'mif':
            #print 'Found a mif, will check for:'
            #print self.absPath.rsplit('.',1)[0] + '.mid'
            return os.path.exists(self.absPath) and (os.path.exists(self.absPath.rsplit('.',1)[0] + '.mid') or os.path.exists(self.absPath.rsplit('.',1)[0] + '.MID'))
            
        elif self.getPathFileExt() == 'mid':
            #print 'Found a mid, will check for the mif'
            return os.path.exists(self.absPath) and (os.path.exists(self.absPath.rsplit('.',1)[0] + '.mif') or os.path.exists(self.absPath.rsplit('.',1)[0] + '.MIF'))
        
        elif self.getPathFileExt() == 'shp':
            return os.path.exists(self.absPath) and os.path.exists(self.absPath.rsplit('.',1)[0].lower() + '.dbf') and os.path.exists(self.absPath.rsplit('.',1)[0].lower() + '.shx')
        
        else:
            return os.path.exists(self.absPath)
            
    def isReal(self):
        return self.real
        
    def find(self, audit):
    
        allFiles = audit.getModelFiles() + audit.getOtherFiles()
        result = ''
        
        for f in allFiles:
            if f.getName() == self.pathFileName:
                result = f.getFilePath()
                break
            else:
                pass    #doc.WriteLine ('Searching... ' + f.getFilePath())
                
        return result
            
class TCF_file(ModelFile):
    '''
        Class for TCF model files
    '''
    def __init__(self, filepath):
        ModelFile.__init__(self, filepath)
        
    def PathSearch(self):
        # Use 'File ' not 'File' as this picks up all 'File Read' commands and misses 'Write Files' commmands
        return ModelFile.PathSearch(self, ['File ', 'BC Database', 'Read'], '!', '==')
        
    #def GIS_Search(self):
    #    return ModelFile.PathSearch(self, ['MI Projection'], '!', '==')
        
    
class ECF_file(ModelFile):
    '''
        Class for TCF model files
    '''
    def __init__(self, filepath):
        ModelFile.__init__(self, filepath)
        
    def PathSearch(self):
        return ModelFile.PathSearch(self, ['Read', 'Data'], '!', '==')
        

class TBC_file(ModelFile):
    '''
        Class for TBC model files
    '''
    def __init__(self, filepath):
        ModelFile.__init__(self, filepath)
        
    def PathSearch(self):
        return ModelFile.PathSearch(self, ['BC Database', 'Read'], '!', '==')
        
class TGC_file(ModelFile):
    '''
        Class for TGC model files
    '''
    def __init__(self, filepath):
        ModelFile.__init__(self, filepath)
        
    def PathSearch(self):
        return ModelFile.PathSearch(self, ['Read'], '!', '==')
        
class TEF_file(ModelFile):
    '''
        Class for TEF model files
    '''
    def __init__(self, filepath):
        ModelFile.__init__(self, filepath)
        
    def PathSearch(self):
        return []
        
class IEF_file(ModelFile):
    '''
        Class for IEF model files
    '''
    def __init__(self, filepath):
        ModelFile.__init__(self, filepath)        
    def PathSearch(self):
        return ModelFile.PathSearch(self, ['Datafile', 'InitialConditions', 'EventData', '2DFile'], splitOn = '=')
        
# file extension pointing the the associated paths. trd files follow the same format as tcf files hence share the same class
model_file_exts = {'tcf': TCF_file, 'trd': TCF_file, 'ecf': ECF_file, 'tbc': TBC_file, 'tgc': TGC_file, 'tef': TEF_file, 'ief': IEF_file}
ignore_file_exts = ['log', 'doc']