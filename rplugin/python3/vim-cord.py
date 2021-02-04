import pypresence as rpc
from typing import Optional
import sys
import pynvim
import asyncio
import nest_asyncio
from time import time as nowTime
nest_asyncio.apply()


appId = "746988158629052416"

@pynvim.plugin
class vimCord(object):

    __vim                = None
    __discord            = None
    __currentBufferState = None
    __currentRPCState    = None

    def __getBufferState(self) -> dict:
        bufferState = {}
        bufferState["filetype"]   = self.__vim.eval("&filetype")
        bufferState["filename"]   = self.__vim.eval("expand('%:t')")
        bufferState["modifiable"] = self.__vim.eval("&modifiable")

        self.__currentBufferState = bufferState
        return bufferState


    def __getVariable(self, value: str) -> Optional[str]:
        try:
            return self.__vim.eval(value)
        except:
            return None

    def __getFilenamePrefix(self, modifiable : bool) -> str:
        return "Editing" if modifiable else "Reading"

    def __buildRPCUpdate(self, bufferState : dict, restartTimer : bool) -> dict:
        RPCUpdate = {}

        RPCUpdate["details"]     = f'{self.__getFilenamePrefix(bufferState["modifiable"])}: {bufferState["filename"]}'
        RPCUpdate["start"]       = nowTime() if restartTimer else None #Restart timer?
        RPCUpdate["small_image"] = "vim" #For now just use vim image TODO: Dynamically update based on vim version
        RPCUpdate["large_image"] = bufferState["filetype"] if bufferState["filetype"] != "" else None

        self.__currentRPCState = RPCUpdate
        return RPCUpdate

    #MUST be synchronous or handler will not be registered
    @pynvim.autocmd('VimLeave', allow_nested=False, sync=True)
    def onVimLeave(self):
        self.__discord.clear()
        self.__discord.get_event_loop().stop() #Maybe don't stop this loop?
        self.__discord.close()
        self.__vim.close()
        sys.exit(0)

    @pynvim.autocmd('BufEnter', allow_nested=True, sync=False)
    def onBufferEnter(self):
        bufferState : dict = self.__getBufferState()
        #TODO: Memoization algorithm for open buffers to cache timers?
        RPCUpdate   : dict = self.__buildRPCUpdate(bufferState, restartTimer=True) #Always restart timer when new buffer is entered
        self.__discord.update(**RPCUpdate)

    #This apparently only runs after buffer is written to disk TODO: Find way to run async?
    @pynvim.autocmd('BufModifiedSet', allow_nested=True, sync=False, eval="&modifiable")
    def onBufferModifiedSet(self, newModifiable : int):
        if self.__currentBufferState != None and self.__currentBufferState["modifiable"] != newModifiable:
            self.__currentRPCState["details"] = f'{self.__getFilenamePrefix(newModifiable)}: {self.__currentBufferState["filename"]}'
            self.__discord.update(**self.__currentRPCState)
            self.__currentBufferState["modifiable"] = newModifiable

    def __init__(self, vim):
        self.__vim = vim

        #Set this variable in your vimrc/init.vim to disable vim-cord
        isLoaded = self.__getVariable("g:loaded_vim_cord")
        if isLoaded != None:
            self.__vim.quit()
            sys.exit(0)

        assert isLoaded == None

        try:
            discord = rpc.Presence(client_id = appId)
            discord.connect()
            discord.clear()

            self.__discord = discord
        except:
            self.__vim.close()
            sys.exit(0)

        

