from pypresence import Presence
import time
import sys
import pynvim
import nest_asyncio
import threading
nest_asyncio.apply() #Apply asyncio patch

nvim_client_id = "746627198458527816" #Neovim client_id
vim_client_id  = "746988158629052416" #Vim client_id

def get_position_line(nvim):
    line = nvim.eval("line('.')")
    col  = nvim.eval("col('.')")
    last_line = nvim.eval("line('$')")

    return str(col) + ":" + str(line) + " / " + str(last_line)
    
filetype_to_tooltip = {
        "vim"       : "Vim",
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
        modifiable    = 0
        image         = "vim"
        large_tooltip = "Vim Help File"
    elif filetype == "qf":
        filename = 
    elif filetype == "netrw":
        details_line  = "Exploring directories"
        modifiable    = 0
        image         = "vim"
        large_tooltip = "Netrw File Explorer"
    elif filetype == "nerdtree":
        details_line  = "Exploring directories"
        modifiable    = 0
        image         = "vim"
        large_tooltip = "NERDTree File Explorer"
    else:
        filename      = nvim.eval("@%")
        modifiable    = nvim.eval("&modifiable") #Boolean 0/1
        image         = filetype 
        large_tooltip = filetype_to_tooltip.get(filetype)
        details_prefix = 'Editing' if modifiable == 1 else 'Reading'
        details_line = details_prefix + " " + filename


    position_line = get_position_line(nvim)
   
    if reset_timer:
        RPC.update( details = details_line, state = position_line, large_image = image, large_text = large_tooltip, small_image = SMALL_IMAGE, start = time.time() * 1000 )
    else:
        RPC.update( details = details_line, state = position_line, large_image = image, large_text = large_tooltip, small_image = SMALL_IMAGE)

@pynvim.plugin
class vim_cord(object):

    @pynvim.autocmd('BufEnter', pattern='*', allow_nested=True, sync=False)
    def bufenter(self):
        send_update(self.nvim, True)

    def __init__(self, nvim):
        global RPC
        global EDITOR
        global SMALL_IMAGE
        self.nvim = nvim
        
        try:
            #Editor name can be 'vim' or 'neovim', it defines the small_image icon
            EDITOR = nvim.eval('g:vim_cord_editor_name')
            if EDITOR == "":
                EDITOR = "nvim"
            elif EDITOR != "nvim" and EDITOR != "vim":
                nvim.err_write("Invalid editor name " + EDITOR + ", expected 'vim' or 'nvim'\n")
                sys.exit(1)
            
            if EDITOR == "vim":
                RPC = Presence(vim_client_id)
                SMALL_IMAGE = "vim"
            elif EDITOR  == "nvim":
                RPC = Presence(nvim_client_id)
                SMALL_IMAGE = "nvim"

            RPC.connect()

        except ConnectionRefusedError:
            #Discord not open
            sys.exit(0);

        
         



        
    

