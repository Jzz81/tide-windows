#-------------------------------------------------------------------------------
# Name:        Database.py
# Purpose:     Hold code to do all database works
#
# Author:      Joos Dominicus
#
# Created:     01-05-2014
#-------------------------------------------------------------------------------

import urllib2
import git
import os

def internet_on():
    '''checks if there is an internet connection by pinging github'''
    try:
        urllib2.urlopen("http://192.30.252.128", timeout=1)
        return True
    except:
        return False

class GitPull():
    '''Class that handles a git pull for the tidal data'''
    def __init__(self, parent, repo_path):
        self.parent = parent
        self.repo_path = repo_path
        self.__git_init()

    def __git_init(self):
        '''inits a git repo in the designated folder.'''
        # The git module only allows bare repos
        g = git.Git(self.repo_path)
        g.execute("git init")
        g.execute(["remote", "add", "origin", "http://github.com/Jzz81/tidal-data.git"])

    def __git_pull(self):
        '''pulls the data from github'''
        pass

    def __path_is_git_repo(self):
        '''determines if the given path is a git repo'''
        try:
            self.git_repo = git.Repo(self.repo_path)
            return True
        except git.InvalidGitRepositoryError:
            return False


def main():
##    print internet_on()
    dir = "{0}\jzz_pWesp".format(os.environ["LOCALAPPDATA"])
    git_repo_path = dir + "\\tidal_data_repo"
    if not os.path.exists(git_repo_path):
        os.makedirs(git_repo_path)
    self = object
    gp = GitPull(self, git_repo_path)


if __name__ == '__main__':
    main()
