from pypresence import Presence #Discord RPC API
import time
import threading
import pynvim                   #Python<->Neovim Integration
import nest_asyncio             #Asyncio patch
nest_asyncio.apply()            #Apply asyncio patch for nested event loop

nvim_client_id = "746627198458527816" #Neovim client_id
vim_client_id  = "746988158629052416" #Vim client_id

default_small_text_message = "Vim, but even better."

RPC = None
current_state = None

#Huge dictionary to convert vim filenames to proper display names, the distinction is necessary as
#the vim names are used for the assets while the proper names are for discord hover tooltips
ft_to_pml = {
        "vim"       : "Vimscript",
        "python"    : "Python",
        "c"         : "C Lang",
        "cpp"       : "C++",
        "potion"    : "Potion",
        "javascript": "JavaScript",
        "html"      : "HTML",
        "rust"      : "Rust",
        "ruby"      : "Ruby"
}

class vim_state(object):
    filetype: str
    pml     : str

    def __init__(self, filename : str, filetype : str, pml : str):
        self.filename = filename
        self.filetype = filetype
        self.pml      = pml


def line_to_lline(c_line, c_col,l_max):
    return c_col + ":" + c_line + " / " + l_max

def get_state(nvim):
    filename = nvim.command_output("echo expand('%:t')")
    filetype = nvim.command_output("echo &ft")
    pml      = ft_to_pml.get(filetype)
    return vim_state(filename, filetype, pml)

def send_update(state, RPC, small_text):
    global current_state

    pml = ft_to_pml.get(state.filetype)

    RPC.update( details     = state.filename,
                large_image = state.filetype,
                large_text  = pml,
                small_image = "neovim",
                small_text  = small_text,
                start       = time.time() * 1000)
    current_state = state

def connect(editor_name):
    global RPC
    if editor_name.lower() == "vim":
        RPC = Presence(vim_client_id)
    else:
        RPC = Presence(nvim_client_id)
    RPC.connect()




@pynvim.plugin
class vim_cord(object):

    def __init__(self, nvim):
        self.nvim = nvim

        # Get Editor name from vim, first it looks for the User defined variable, if not present
        # It will try for Neovim, if that is also not present, returns Vim
        editor_name = nvim.command_output("if exists('g:vim_cord_editor_name')  | \
                                            echo g:vim_cord_editor_name         | \
                                            elseif has('nvim')                  | \
                                            echo 'Neovim'                       | \
                                            else                                | \
                                            echo 'Vim'                          | \
                                            endif")

        self.small_text = nvim.command_output("if exists('g:vim_cord_small_image_tooltip')  | \
                                                echo g:vim_cord_small_image_tooltip         | \
                                                else                                        | \
                                                echo '" + default_small_text_message + "'   | \
                                                endif")
        connect(editor_name)
        thread_loop = threading.Thread(target=vim_cord.run_loop)
        thread_loop.start()


    #CHange to thraeded interface
    def run_loop(self):
        self.nvim.command("split")
        line    = nvim.command_output("echo line('.')")
        column  = nvim.command_output("echo col('.')")
        lline   = nvim.command_output("echo line('$')")
        RPC.update( details     = current_state.filename,
                    large_image = state.filetype,
                    small_image = "neovim",
                    small_text  = self.small_text,
                    state       = line_to_lline(line, column, lline))
        time.sleep(15)

    # Send update immediately when entering new buffer!
    @pynvim.autocmd('BufEnter', pattern='*', eval=None, allow_nested=True, sync=False)
    def on_bufenter(self):
        send_update(get_state(self.nvim), RPC, self.small_text)

    #Clear Presence and shutdown connection with discord when vim is about to exit
    @pynvim.autocmd('VimLeave', pattern='*', eval=None, allow_nested=True, sync=False)
    def on_vim_leave(self):
        RPC.clear()
