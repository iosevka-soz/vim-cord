from pypresence import Presence
import sys
import pynvim
import time
import nest_asyncio
nest_asyncio.apply() #Apply asyncio patch

nvim_client_id = "746627198458527816" #Neovim client_id
vim_client_id  = "746988158629052416" #Vim client_id

filetype_to_tooltip = {
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

    if filetype == "help":
        filename      = nvim.command_output("echo expand('%:t')")
        image         = "vim"
        large_tooltip = "Vim Help File"
    elif filetype == "qf":
        details_line  = "Quickfix Menu"
        image         = "vim"
        large_tooltip = "Vim Quickfix"
    elif filetype == "netrw":
        details_line  = "Exploring directories"
        image         = "vim"
        large_tooltip = "Netrw File Explorer"
    elif filetype == "nerdtree":
        details_line  = "Exploring directories"
        image         = "vim"
        large_tooltip = "NERDTree File Explorer"
    else:
        filename      = nvim.eval("expand('%:t')")
        if filename == "":
            details_line = "Editing an Unnamed Buffer"
            image = "None"
        else:
            modifiable    = nvim.eval("&modifiable") #Boolean 0/1
            details_prefix = 'Editing:' if modifiable == 1 else 'Reading:'
            details_line = details_prefix + " " + filename
            image         = filetype
            large_tooltip = filetype_to_tooltip.get(filetype)

    RPC.update( details = details_line,
                large_image = image if image != "None" else None,
                large_text = large_tooltip if image != "None" else None,
                small_image = SMALL_IMAGE,
                small_text = SMALL_IMAGE_TOOLTIP,
                start = time.time() * 1000 if reset_timer else None)

@pynvim.plugin
class vim_cord(object):

    @pynvim.autocmd('BufEnter', pattern='*', allow_nested=True, sync=False)
    def bufenter(self):
        if not DISABLED:
            send_update(self.nvim, True)

    def __init__(self, nvim):
        global RPC
        global DISABLED
        global EDITOR
        global SMALL_IMAGE
        global SMALL_IMAGE_TOOLTIP
        self.nvim = nvim

        try:
            nvim.eval('g:loaded_vim_cord')
            DISABLED = True
        except pynvim.api.common.NvimError:
            DISABLED = False
            try:
                #Editor name can be 'vim' or 'neovim', it defines the small_image icon
                #Tries to find the user defined variable, if it doesn't exist, check if is nvim, if not use vim
                try:
                    EDITOR = nvim.eval('g:vim_cord_editor_name')
                    if EDITOR != "nvim" and EDITOR != "vim":
                        nvim.err_write("Invalid editor name " + EDITOR + ", expected 'vim' or 'nvim'\n")
                        sys.exit(1)
                except pynvim.api.common.NvimError:
                    EDITOR = 'nvim' if nvim.eval("has('nvim')") else 'vim'

                if EDITOR == "vim":
                    RPC = Presence(vim_client_id)
                    SMALL_IMAGE = "vim"
                elif EDITOR  == "nvim":
                    RPC = Presence(nvim_client_id)
                    SMALL_IMAGE = "nvim"
                #Check for user defined tooltip for small_image
                try:
                    SMALL_IMAGE_TOOLTIP  = nvim.eval('g:vim_cord_small_image_tooltip')
                except pynvim.api.common.NvimError:
                    SMALL_IMAGE_TOOLTIP = 'Vim' if EDITOR == 'vim' else 'Neovim'

                RPC.connect()

            except ConnectionRefusedError:
                #Discord not open
                sys.exit(0);
