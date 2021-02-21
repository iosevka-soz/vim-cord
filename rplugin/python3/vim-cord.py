from pypresence import Presence
from pypresence import exceptions
from typing import Optional
from typing import Union
import time
import sys
import pynvim
import asyncio
import nest_asyncio

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

    #Init with default values.
    config      = { 
                    "discord_retry"       : True,
                    "discord_retry_delay" : 10,
                    "discord_max_retry"   : 3,
                    "track_modifiable"    : True }

    def getVar(self, value: str):
        try:
            return self.vim.eval(value)
        except:
            return None


    def parseEditorName(self) -> str:
        editors = ['vi', 'vim', 'neovim', 'gvim', 'macvim' ]
        nameOverride = self.getVar("g:vim_cord_editor_override")

        def getFromEnv() -> str:
            macvim = self.vim.command_output("if has('gui_macvim') | echo 1 | endif")
            if not macvim:
                gvim = self.vim.command_output("if has('gui_running') | echo 1 | endif")
                if not gvim:
                    nvim = self.vim.command_output("if has('nvim') | echo 1 | endif")
                    if not nvim:
                        return 'vim'
                    return 'neovim'
                return 'gvim'
            return 'macvim'

        if nameOverride != None:
            if nameOverride in editors:
                return nameOverride
            else:
                self.vim.err_write(f'Invalid editor name {nameOverride}.\n')
                self.disabled = True
                return None

        return getFromEnv()

    def parseAppId(self) -> str:
        appIdOverride = self.getVar("vim_cord_app_id_overide")
        if appIdOverride != None:
            return appIdOverride

        editorName = self.config["editor"]
        nonDefault = self.getVar(f'g:vim_cord_{editorName}_app_id')
        return nonDefault if nonDefault != None else {
                                                      "vi"     : "809799093873278976",
                                                      "vim"    : "746988158629052416",
                                                      "neovim" : "746627198458527816",
                                                      "gvim"   : "809799169308098668",
                                                      "macvim" : "809799485327671317"
                                                     }[editorName]

    def parseConfig(self) -> dict:
        prefix = "g:vim_cord"
        def confSet(key : str, val : str):
            self.config[key] = val

        def confAppend(key : str, varSuffix : str):
            val = self.getVar(f'{prefix}_{varSuffix}')
            if val != None:
                confSet(key, val)
        
        confSet("editor",                 self.parseEditorName())
        confSet("discord_app_id",         self.parseAppId())
        confAppend("discord_retry",       "discord_retry")
        confAppend("discord_max_retry",   "max_retry")
        confAppend("discord_retry_delay", "retry_delay")
        confAppend("track_modifiable",    "track_modifiable") 
        return self.config


    def discordConnect(self, retry : Optional[bool], maxRetries : Optional[int], retryDelay : Optional[int]) -> Optional[Presence]:
        retry      = retry      if retry      != None else self.config["discord_retry"]
        maxRetries = maxRetries if maxRetries != None else self.config["discord_max_retry"]
        retryDelay = retryDelay if retryDelay != None else self.config["discord_retry_delay"]

        rpc = Presence(client_id = self.config["discord_app_id"])
        def tryConnect() -> bool:
            try:
                rpc.connect()
                return True
            except:
                return False
        
        if tryConnect():
            return rpc
        elif retry:
            retryCount = 1
            self.vim.err_write(f'Discord connection failed, retrying {retryCount}/{maxRetries} in {retryDelay} seconds...\n')
            time.sleep(retryDelay)
            while not tryConnect():
                retryCount += 1
                if retryCount >= maxRetries:
                    self.vim.err_write(f'Max retries exceeded {retryCount}/{maxRetries}, disabling vim-cord\n')
                    self.disabled = True
                    return None
                self.vim.err_write(f'Discord connection failed, retrying {retryCount}/{maxRetries} in {retryDelay} seconds...\n')
                time.sleep(retryDelay)
            self.vim.out_write("Connection retry succeeded!\n")
            return rpc
    
    #MUST be synchronous or handler will not be registered
    @pynvim.autocmd('VimLeave', allow_nested=False, sync=True)
    def onVimLeave(self):
        if self.disabled:
            pass
        self.discord.clear()
        self.discord.close()

    def parseBufState(self) -> dict:
        state = {}
        def evalState(key : str, eval : str):
            state[key] = self.vim.eval(eval)

        def setState(key : str, val :str):
            state[key] = val

        evalState("filetype", "&filetype")
        evalState("filename", "expand('%:t')")
        if self.config["track_modifiable"]:
            evalState("isModifiable",     "&modifiable")
            setState("prefix", ("Editing" if state["isModifiable"] else "Reading"))
        else:
            setState("prefix", "Editing")
        self.bufState = state
        return state

    def buildRPCUpdate(self) -> dict:
        rpc = {}
        def setRPC(key : str, val : str):
            rpc[key] = val

        setRPC("details",     f'{self.bufState["prefix"]}: {self.bufState["filename"]}')
        setRPC("small_image", self.config["editor"])
        setRPC("large_image", self.bufState["filetype"])
        self.rpcState = rpc
        return rpc

    def updatePresence(self, rpc : dict):
        try:
            self.discord.update(**rpc)
        except exceptions.InvalidID:
            self.disabled = True

    @pynvim.autocmd('BufEnter', allow_nested=True, sync=False)
    def onBufEnter(self):
        #TODO: Deferred evaluation of self.discord not to miss current buffer.
        if self.disabled or self.discord == None: #Discord being none means plugin hasn't finished startup
            pass
        currentBufferState = self.parseBufState()
        self.bufState = currentBufferState
        self.updatePresence(self.buildRPCUpdate())

    @pynvim.autocmd('BufModifiedSet', allow_nested=True, sync=False, eval="&modifiable")
    def onBufModifiedSet(self, newModifiable : int):
        if self.disabled or not self.config["track_modifiable"] or newModifiable == self.bufState["isMod"]:
            pass
        self.bufState["isModifiable"] = newModifiable
        self.bufState["prefix"] = "Editing" if self.bufState["isModifiable"] else "Reading"
        self.rpcState["details"] = f'{self.bufState["prefix"]}: {self.bufState["filename"]}'
        self.updatePresence(self.rpcState)

    @pynvim.command('VimCordReconnect', 0, sync=False)
    def VimCordRetry(self):
        if self.getVar("g:loaded_vim_cord") == None:
            self.vim.out_write("Vim-cord is disabled\n")
            pass
        if self.discord != None:
            self.discord.clear()
            self.discord.close()

        if self.discordConnect(None, None, None) != None:
            self.disabled = False

    def __init__(self, vim):
        #Set this variable in your vimrc/init.vim to disable vim-cord
        if self.getVar("g:loaded_vim_cord") != None:
            self.disabled = True

        self.vim     = vim
        self.config  = self.parseConfig()
        self.discord = self.discordConnect(None, None, None)

