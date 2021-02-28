from pypresence import Presence, exceptions
from typing import Optional
from threading import Thread
import asyncio
import time
import sys
import pynvim
import nest_asyncio

nest_asyncio.apply()

@pynvim.plugin
class vimCord(object):

    ready = False
    startTime = None
    bufferStart = None
    hardDisabled = False
    disabled = False

    activeBuffer = -1
    buffers = {} #Dict : Dict
    timers  = {} #Dict : start, left

    disc = None
    
    #Defaults
    conf = { "alertOnSuccess" : True,
             "alertOnFail"    : True,
             "noSmallImg"     : False,
             "noImg"          : False,
             "updateDelay"    : 15,
             "contractBytes"  : True, 
             "bytes1000"      : False,
             "timerTracking"  : 'buffer_remember' }

    def getVar(self, value: str):
        try:
            return self.vim.eval(value)
        except:
            return None

    ##############################################
    # Parsing Config #############################
    ##############################################
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

        if nameOverride is not None:
            if nameOverride in editors:
                return nameOverride
            else:
                self.vim.err_write(f'Invalid editor name {nameOverride}.\n')
                self.disabled = True
                return None
        return getFromEnv()

    def parseAppId(self, editorName) -> str:
        appIdOverride = self.getVar("vim_cord_app_id_overide")
        if appIdOverride is not None:
            return appIdOverride

        nonDefault = self.getVar(f'g:vim_cord_{editorName}_app_id')
        return nonDefault if nonDefault != None else {
                                                      "vi"     : "809799093873278976",
                                                      "vim"    : "746988158629052416",
                                                      "neovim" : "746627198458527816",
                                                      "gvim"   : "809799169308098668",
                                                      "macvim" : "809799485327671317"
                                                     }[editorName]

    def parseConfig(self):
        configuration = {}
        def confSet(key : str, val : str):
            configuration[key] = val

        def confAppend(key : str, varSuffix : str):
            val = self.getVar(f'g:vim_cord_{varSuffix}')
            if val is not None:
                confSet(key, val)
        
        confSet("editor",             self.parseEditorName())
        confSet("appId",              self.parseAppId(configuration["editor"]))
        confAppend("alertOnSuccess",  "alert_connection_success")
        confAppend("alertOnFail",     "alert_on_fail")
        confAppend("noSmallImg",      "disable_small_image")
        confAppend("noImg",           "disable_image")    
        confAppend("updateDelay",     "update_delay")
        confAppend("contractBytes",   "contract_bytes")
        confAppend("bytes1000",       "bytes_1000")
        confAppend("timerTracking",   "timer_tracking_type")
        return configuration

    ##############################################

    def bytesToSI(self, val : int) -> str:
        si = { 0 : 'B',
               1 : 'kB',
               2 : 'MB',
               3 : 'GB',
               4 : 'TB' } if self.conf["bytes1000"] else { 0 : 'B',
                                                           1 : 'kiB',
                                                           2 : 'MiB',
                                                           3 : 'GiB',
                                                           4 : 'TiB'  }
        iterations  = 0
        oldval = val
        while True:
            if self.conf["bytes1000"]:
                val /= 1000
            else:
                val /= 1024
            if val < 1:
                break
            oldval = val
            iterations += 1
        return f'{"%.2f"%(oldval)}{si[iterations]}' 

    def getBufferInfo(self, bufnum : int) -> dict:
        tempState = {}
        def stateSet(k, v):
            var = self.getVar(v)
            tempState[k] = None if var == '' else var

        stateSet("fn", "expand('%:t')") #Filename
        stateSet("ft", "&filetype") #Filetype
        stateSet("cln", "line('.')")
        stateSet("mln", "line('$')")
        stateSet("col", "col('.')")
        stateSet("fs", "getfsize(expand(@%))")
        stateSet("mod", "&modifiable")
        self.buffers[bufnum] = tempState
        return tempState

    def updateRPC(self, buf : dict, time : float):
        def bufferToRPC() -> dict:
            tmpRPC = {}
            if not self.conf["noImg"]:
                tmpRPC["large_image"] = buf["ft"]
                ft = buf["ft"]
                tmpRPC["large_text"] = ("CLang" if ft == 'c' else ft.capitalize()) if ft is not None else None
            if not self.conf["noSmallImg"]:
                tmpRPC["small_image"] = self.conf["editor"]
                tmpRPC["small_text"] = self.conf["editor"].capitalize()

            tmpRPC["details"] = f'{"Editing" if buf["mod"] else "Reading"}: {buf["fn"]}'
            filesize = self.bytesToSI(buf["fs"]) if self.conf["contractBytes"] else buf["fs"]
            tmpRPC["state"] = f'{buf["cln"]}/{buf["mln"]}:{buf["col"]} - {filesize}'
            if time is None or self.conf["timerTracking"] == 'session':
                tmpRPC["start"] = self.startTime
            else:
                tmpRPC["start"] = time
            return tmpRPC
        
        assert self.disc is not None
        self.disc.update(**bufferToRPC())

    #Attempt connection to discord
    def discordConnect(self) -> Optional[Presence]:
        presence = Presence(client_id = self.conf["appId"])
        try:
            presence.connect()
            if self.conf["alertOnSuccess"]:
                self.vim.out_write(f'[Vim-Cord] Connection successful!\n')
            return presence
        except:
            if self.conf["alertOnFail"]:
                self.vim.err_write(f'[Vim-Cord] Connection failed\n')
            self.disabled = True
            return None

    def periodicUpdater(self):
        def doUpdate():
            tt = self.conf["timerTracking"]
            time = None
            if tt == 'session':
                time = self.startTime
            elif tt == 'buffer':
                time = self.bufferStart
            elif tt == 'buffer_remember':
                time = self.timers[self.activeBuffer]["rpc"]

            buffer = self.getBufferInfo(self.activeBuffer)
            self.updateRPC(buffer, time)

        while True:
            if self.ready:
                time.sleep(self.conf["updateDelay"])
                self.vim.async_call(doUpdate)
        
    ###################################################
    # Vim Autocommands ################################
    ###################################################
    @pynvim.autocmd('VimLeavePre', allow_nested=False, sync=True)
    def onVimClose(self):
        if self.ready:
            assert self.disc is not None
            self.disc.clear()
            self.disc.close()

    @pynvim.autocmd('BufEnter', allow_nested=False, sync=False, eval="bufnr()")
    def onBufEnter(self, bufnum : int):
        if self.ready:
            if bufnum not in list(self.buffers.keys()): #This is a new buffer
                self.getBufferInfo(bufnum)
            self.buffers[bufnum]["active"] = True
            now = time.time()
            rpcTime = None
            if self.conf["timerTracking"] == 'buffer_remember':
                if bufnum in list(self.timers.keys()):
                    rpcTime = now - (self.timers[bufnum]["left"] - self.timers[bufnum]["start"]) #Now minus differenct between when started and left
                    self.timers[bufnum]["rpc"] = rpcTime
                else:
                    self.timers[bufnum] = {}
                    rpcTime = now
                    self.timers[bufnum]["start"] = now #Set starting time because it's a new buffer
                    self.timers[bufnum]["left"] = now
                    self.timers[bufnum]["rpc"] = now
            elif self.conf["timerTracking"] == 'buffer':
                self.bufferStart = now
                rpcTime = now
            
            self.activeBuffer = bufnum
            self.updateRPC(self.buffers[bufnum], rpcTime) #Update discord on current buffer

    @pynvim.autocmd('BufLeave', allow_nested=False, sync=False, eval="bufnr()")
    def onBufLeave(self, bufnum : int):
        if self.ready:
            assert bufnum in list(self.buffers.keys())
            assert self.disc is not None
            self.disc.clear() #Clear RPC as fast as possible
            self.buffers[bufnum]["active"] = False
            if self.conf["timerTracking"] == 'buffer_remember':
                self.timers[bufnum]["left"] = time.time()

    @pynvim.autocmd('BufDelete', allow_nested=False, sync=False, eval="bufnr()")
    def onBufDelete(self, bufnum : int):
        #Just remove buffer from list of active buffers
        if self.ready:
            self.buffers.pop(bufnum, None)
            self.timers.pop(bufnum, None)

    ###################################################
    # Vim Commands ####################################
    ###################################################
    @pynvim.command('VimCordReconnect')
    def VimCordReconnect(self):
        if self.hardDisabled:
            self.vim.err_write("[Vim-cord] Plugin is hard disabled by setting loaded_vim_cord variable\n")
        else:
            self.conf = self.parseConfig()
            self.disc = self.discordConnect()
            if self.disc is not None:
                self.disabled = False
                self.ready = True
            else:
                if self.conf["alertOnFail"]:
                    self.vim.err_write(f'[Vim-cord] Reconnection failed\n')

    @pynvim.command('VimCordDisconnect')
    def VimCordDisconnect(self):
        if self.hardDisabled:
            self.vim.err_write("[Vim-cord] Plugin is hard disabled by setting loaded_vim_cord variable\n")
        elif not self.ready:
            self.vim.err_write("[Vim-cord] Not connected to discord.\n")
        else:
            assert self.disc is not None
            self.disc.clear()
            self.disc = None
            self.disabled = True
            self.ready = False
            self.vim.out_write("[Vim-cord] Discord RPC disconnected.")

    def __init__(self, vim):
        self.vim = vim 
        try:
            #Set this variable in your vimrc/init.vim to disable vim-cord
            vim.eval("g:loaded_vim_cord")
            self.hardDisabled = True
            self.disabled = True
        except pynvim.api.common.NvimError:
            self.conf = {**self.conf, **self.parseConfig()} #Merge parsed config with defaults appropriately
            self.disc = self.discordConnect()
            if self.disc is not None:
                self.ready = True
                if self.conf["updateDelay"] > -1:
                    Thread(target=self.periodicUpdater).start()
                    self.startTime = time.time()
            else:
                self.disabled = True
