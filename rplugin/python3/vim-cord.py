from pypresence import Presence
import sys
import pynvim
import time
import nest_asyncio
nest_asyncio.apply() #Apply asyncio patch

nvim_client_id = "746627198458527816" #Neovim client_id
vim_client_id  = "746988158629052416" #Vim client_id

ft_to_tp = {
        "vim"       : "Vimscript",
        "nvim"      : "Neovim",
        "c"         : "C Language",
        "cpp"       : "C++",
        "javascript": "JavaScript",
        "java"      : "Java",
        "html"      : "HTML",
        "python"    : "Python",
        "rust"      : "Rust",
        "potion"    : "Potion",
        "ruby"      : "Ruby",
}

def send_update(nvim, reset_timer : bool):

    filetype = nvim.eval("&ft")
    filename = nvim.eval("expand('%:t')")

    if filetype in [ "help", "qf", "netrw", "nerdtree" ]:
        image = "vim"
    else:
        image = None if not filename or filetype not in ft_to_tp.keys() else filetype

    large_tp_switcher = { 
            "help"     : "Help File",
            "qf"       : "Vim Quickfix",
            "netrw"    : "Netrw File Explorer",
            "nerdtree" : "NERDTree File Explorer"
            }

    large_tooltip = large_tp_switcher.get(filetype, ft_to_tp.get(filetype)) if image != None else None

    details_switcher = {
            "qf"       : "Quickfix Menu",
            "netrw"    : "Exploring directories",
            "nerdtree" : "Exploring directories"
            }

    def mod_prefix():
        return 'Editing:' if nvim.eval('&modifiable') else 'Reading:'
    
    details_line = details_switcher.get(filetype, "Editing an Unnamed Buffer" if not filename else f'{mod_prefix()} {filename}')
        
    RPC.update( details = details_line,
                large_image = image,
                large_text = large_tooltip,
                small_image = SMI,
                small_text = SMI_TOOLTIP,
                start = time.time() * 1000 if reset_timer else None)

@pynvim.plugin
class vim_cord(object):

    @pynvim.autocmd('BufEnter', pattern='*', allow_nested=True, sync=False)
    def bufenter(self):
        send_update(self.nvim, True)

    @pynvim.autocmd('VimLeave', pattern='*', allow_nested=True, sync=False)
    def vim_leave(self):
        RPC.clear()
        RPC.close()

    def __init__(self, nvim):
        global RPC
        global SMI_TOOLTIP
        global SMI

        def get_var(var : str):
            try:
                return nvim.eval(var)
            except pynvim.api.common.NvimError:
                return None

        loaded = get_var('g:loaded_vim_cord')
        if loaded != None:
            nvim.close()
            sys.exit(0)

        editor_name = get_var('g:vim_cord_editor_name')
        if editor_name != None:
            if editor_name not in ["nvim", "vim"]:
                nvim.err_write( f'Invalid editor name: {editor_name}, expected ''vim'' or ''nvim''')
                nvim.close()
                sys.exit(1)
        else:
            editor_name = 'nvim' if nvim.eval("has('nvim')") else 'vim'

        SMI = 'nvim'

        SMI_TOOLTIP  = get_var('g:vim_cord_small_image_tooltip')
        if SMI_TOOLTIP == None:
            SMI_TOOLTIP = editor_name.title()

        self.nvim = nvim
        RPC = Presence(vim_client_id if editor_name == 'vim' else nvim_client_id)

        try:
            RPC.connect()
        except ConnectionRefusedError:
            print
            nvim.close()
            sys.exit(0)
