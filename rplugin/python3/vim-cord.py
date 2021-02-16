from pypresence import Presence
from typing import Optional
import sys
import pynvim
import asyncio
import nest_asyncio
from time import time as nowTime
nest_asyncio.apply()

@pynvim.plugin
class vimCord(object):

    openBuffers = []
    disabled    = False
    editorName  = True
    vim         = None
    discord     = None
    bufState    = {}
    rpcState    = {}
    config      = {}

    def getVariable(self, value: str):
        try:
            return self.vim.eval(value)
        except:
            return None

    def parseBufState(self) -> dict:
        self.bufState["ftype"] = self.getVariable("&filetype")
        self.bufState["fname"] = self.getVariable("expand('%:t')")
        self.bufState["isMod"] = self.getVariable("&modifiable")
        self.bufState["modPrefix"] = "Editing" if self.bufState["isMod"] else "Reading"
        return self.bufState

    def parseEditorName(self, override : Optional[str]) -> str:
        def getVimOrNvimFromEnv() -> str:
            return "neovim" if self.vim.command_output("if has('nvim') | echo 1 | endif") else "vim"

        if not override:
            return getVimOrNvimFromEnv()

        override = override.lower()
        editorOptions = [ 'vi', 'vim', 'gvim', 'macvim', 'neovim' ]

        if override in editorOptions:
            return override
        else:
            self.vim.err_write(f'Invalid editor name!') #TODO: add editor names on error output
            return getVimOrNvimFromEnv()

    def parseAppId(self, override, editorName) -> str:
        return override if override else  {
                                            "vi"     : "809799093873278976",
                                            "vim"    : "746988158629052416",
                                            "neovim" : "746627198458527816",
                                            "gvim"   : "809799169308098668",
                                            "macvim" : "809799485327671317"
                                          }[editorName]

    def parseConfig(self) -> dict:
        prefix = "g:vim_cord"
        self.config["editor"] = self.parseEditorName(self.getVariable(f'{prefix}_editor_override'))
        self.config["discord_app_id"] = self.parseAppId(self.getVariable(f'{prefix}_app_id'), self.config["editor"])
        self.config["discord_retry"]     = self.getVariable(f'{prefix}_discord_retry')
        self.config["discord_max_retry"] = self.getVariable(f'{prefix}_max_retry')
        self.config["track_modifiable"]  = self.getVariable(f'{prefix}_track_modifiable')
        return self.config

    def buildRPCUpdate(self, restartTimer : bool) -> dict:
        self.rpcState["details"]     = f'{self.bufState["modPrefix"]}: {self.bufState["fname"]}'
        self.rpcState["start"]       = nowTime() if restartTimer else None #Restart timer?
        self.rpcState["small_image"] = self.config["editor"] 
        self.rpcState["large_image"] = self.bufState["ftype"] if self.bufState["ftype"] != "" else None
        return self.rpcState

    def discordConnect(self, retry : Optional[bool], maxRetries : Optional[int]) -> Optional[Presence]:
        if not retry:
            retry = False
        if not maxRetries:
            maxRetries = 3

        rpc = Presence(client_id = self.config["discord_app_id"])
        def try_connect() -> bool:
            try:
                rpc.connect()
                return True
            except:
                return False

        if try_connect():
            return rpc
        elif retry:
            retryCount = 0
            while not try_connect():
                self.vim.err_write(f'Discord connection failed, retrying {maxRetries - retryCount} more times...\n')
                if retryCount >= maxRetries:
                    self.vim.err_write(f'Discord connection max retries exceeded, exiting\n')
                    self.disabled = True
                    return None
                retryCount += 1
            self.disabled = False
            return rpc
    
    #MUST be synchronous or handler will not be registered
    @pynvim.autocmd('VimLeave', allow_nested=False, sync=True)
    def onVimLeave(self):
        if self.disabled:
            pass
        self.discord.clear()
        self.discord.close()

    @pynvim.autocmd('BufEnter', allow_nested=True, sync=False)
    def onBufEnter(self):
        if self.disabled:
            pass
        self.parseBufState()
        if self.discord != None: 
            self.discord.update(**self.buildRPCUpdate(restartTimer=True))

    @pynvim.autocmd('BufModifiedSet', allow_nested=True, sync=False, eval="&modifiable")
    def onBufModifiedSet(self, newModifiable : int):
        if self.disabled or not self.config["track_modifiable"]:
            pass
        if self.bufState["isMod"] != newModifiable:
            self.bufState["isMod"] = newModifiable
            self.bufState["modPrefix"] = "Editing" if newModifiable else "Reading"
            self.rpcState["details"] = f'{self.bufState["modPrefix"]}: {self.bufState["fname"]}'
            self.discord.update(**self.rpcState)

    @pynvim.command('VimCordReconnect', 0, sync=False, eval="g:vim_cord_discord_max_retry")
    def VimCordRetry(self, maxRetries : int):
        if self.disabled:
            self.vim.out_write("Vim-cord is disabled\n")
            pass
        self.discord.clear()
        self.discord.close()
        if not self.discordConnect(True, maxRetries):
            self.disabled = False

    def __init__(self, vim):
        #Set this variable in your vimrc/init.vim to disable vim-cord
        if self.getVariable("g:loaded_vim_cord") != None:
            self.disabled = True

        self.vim     = vim
        self.config  = self.parseConfig()
        self.discord = self.discordConnect(self.config["discord_retry"], self.config["discord_max_retry"])

