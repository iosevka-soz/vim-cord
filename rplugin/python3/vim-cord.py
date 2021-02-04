from pypresence import Presence
from typing import Optional
import sys
import pynvim
import asyncio
import nest_asyncio
from time import time as nowTime
nest_asyncio.apply()

defaultVimAppId = "746988158629052416"

@pynvim.plugin
class vimCord(object):

    __disabled           = False

    __vim                = None
    __discord            = None
    __currentBufferState = None
    __currentRPCState    = None
    __config             = None

    def getBufferState(self) -> dict:
        bufferState = {}
        bufferState["filetype"]   = self.getVariable("&filetype")
        bufferState["filename"]   = self.getVariable("expand('%:t')")
        bufferState["modifiable"] = self.getVariableBool("&modifiable")

        self.__currentBufferState = bufferState
        return bufferState

    def parseConfig(self) -> dict:
        config = {}
        config["discord_client_id"] = self.getVariable("g:vim_cord_discord_client_id")
        config["discord_retry"]     = self.getVariableBool("g:vim_cord_discord_retry")
        config["discord_max_retry"] = self.getVariable("g:vim_cord_discord_max_retry")
        return config

    def getVariable(self, value: str) -> Optional[str]:
        try:
            return self.__vim.eval(value)
        except:
            return None

    def getVariableBool(self, value: str) -> Optional[bool]:
        try:
            variableValue = self.__vim.eval(value)
            return 1 if variableValue == 1 else 0 if variableValue == 0 else None
        except:
            return None

    def getFilenamePrefix(self, modifiable : bool) -> str:
        return "Editing" if modifiable else "Reading"

    def die(self):
        self.__disabled = True

    def buildRPCUpdate(self, bufferState : dict, restartTimer : bool) -> dict:
        RPCUpdate = {}

        RPCUpdate["details"]     = f'{self.getFilenamePrefix(bufferState["modifiable"])}: {bufferState["filename"]}'
        RPCUpdate["start"]       = nowTime() if restartTimer else None #Restart timer?
        RPCUpdate["small_image"] = "vim" #For now just use vim image TODO: Dynamically update based on vim version
        RPCUpdate["large_image"] = bufferState["filetype"] if bufferState["filetype"] != "" else None

        self.__currentRPCState = RPCUpdate
        return RPCUpdate

    def discordConnect(self, retry : bool, maxRetries : int, cid : str) -> Presence:
        if cid == None:
            cid = defaultVimAppId

        rpc = Presence(client_id = cid)
        def try_connect() -> bool:
            try:
                rpc.connect()
                return True
            except:
                return False

        success : bool = try_connect()
        if success:
            return rpc
        elif retry:
            retryCount : int = 0
            while not try_connect():
                self.__vim.err_write(f'Discord connection failed, retrying...\n')
                if retryCount >= (1 if maxRetries == None else maxRetries):
                    self.__vim.err_write(f'Discord connection max retries exceeded, exiting\n')
                    self.die()
                    return None
                retryCount += 1
            return rpc

    #MUST be synchronous or handler will not be registered
    @pynvim.autocmd('VimLeave', allow_nested=False, sync=True)
    def onVimLeave(self):
        if not self.__disabled:
            self.__discord.clear()
            #self.__discord.get_event_loop().stop() #Maybe don't stop this loop?
            self.__discord.close()

    @pynvim.autocmd('BufEnter', allow_nested=True, sync=False)
    def onBufferEnter(self):
        if not self.__disabled:
            bufferState : dict = self.getBufferState()
            #TODO: Memoization algorithm for open buffers to cache timers?
            RPCUpdate   : dict = self.buildRPCUpdate(bufferState, restartTimer=True) #Always restart timer when new buffer is entered
            self.__discord.update(**RPCUpdate)

    #This apparently only runs after buffer is written to disk TODO: Find way to run async?
    @pynvim.autocmd('BufModifiedSet', allow_nested=True, sync=False, eval="&modifiable")
    def onBufferModifiedSet(self, newModifiable : int):
        if not self.__disabled:
            if self.__currentBufferState != None and self.__currentBufferState["modifiable"] != newModifiable:
                self.__currentRPCState["details"] = f'{self.getFilenamePrefix(newModifiable)}: {self.__currentBufferState["filename"]}'
                self.__discord.update(**self.__currentRPCState)
                self.__currentBufferState["modifiable"] = newModifiable

    def __init__(self, vim):
        #Set this variable in your vimrc/init.vim to disable vim-cord
        isLoaded = self.getVariable("g:loaded_vim_cord")
        if isLoaded != None:
            self.die()

        self.__vim     = vim
        self.__config  = self.parseConfig()
        self.__discord = self.discordConnect(self.__config["discord_retry"],
                                             self.__config["discord_max_retry"],
                                             self.__config["discord_client_id"])
