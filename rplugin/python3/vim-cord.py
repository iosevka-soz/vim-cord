import pypresence as rpc
from typing import Optional
import sys
import pynvim
import asyncio
import nest_asyncio
nest_asyncio.apply()

appId = "746988158629052416"

@pynvim.plugin
class vimCord(object):

    def __getBufferState(self) -> dict:
        bufferState = {}
        bufferState["filetype"]   = self.vim.eval("&filetype")
        bufferState["filename"]   = self.vim.eval("expand('%:t')")
        bufferState["modifiable"] = self.vim.eval("&modifiable")
        return bufferState


    def __getVariable(self, value: str) -> Optional[str]:
        try:
            return self.vim.eval(value)
        except:
            return None

    #MUST be synchronous or handler will not be registered
    @pynvim.autocmd('VimLeave', allow_nested=False, sync=True)
    def onVimLeave(self):
        self.discord.clear()
        self.discord.get_event_loop().stop() #Maybe don't stop this loop?
        self.discord.close()
        self.vim.close()
        sys.exit(0)

    @pynvim.autocmd('BufEnter', allow_nested=True, sync=False)
    def onBufferEnter(self):
        bufferState = self.__getBufferState()
        #self.discord.update(details = (f'{"Editing" if bufferState["modifiable"] else "Reading"}: {bufferState["filename"]}'))
        self.discord.update(details="asd")
        pass


    def __init__(self, vim):
        self.vim = vim

        #Set this variable in your vimrc/init.vim to disable vim-cord
        isLoaded = self.__getVariable("g:loaded_vim_cord")
        if isLoaded != None:
            self.vim.quit()
            sys.exit(0)

        assert isLoaded == None

        try:
            discord = rpc.Presence(client_id = appId)
            discord.connect()
            discord.clear()

            self.discord = discord
        except:
            self.vim.close()
            sys.exit(0)

        

