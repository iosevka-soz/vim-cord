# Vim-Cord

Quick and simple, single file Discord RPC integration for Neovim. (And soon Vim)

# Installation

[Pathogen](https://github.com/tpope/vim-pathogen)
    `git clone https://github.com/iosevka-soz/vim-cord` into your installations Bundle directory.

[Vim-Plug](https://github.com/junegunn/vim-plug)
    Add `Plug 'iosevka-soz/vim-nasm'` to your vimrc's Vim-Plug section.

## Dependencies

- Neovim compiled with Python support (Vim support: incoming)
- Python module pynvim:
    `pip3 install --user pynvim`
- Python module pypresence:
    `pip3 install --user pypresence`
- Python module nest-asyncio
    `pip3 install --user nest-asyncio`

## Usage

It should work out of the box without any configuration needed.

## Configuration

You can disable Vim-Cord entirely:
`g:loaded_vim_cord` Set it to anything to disable it.

You can make Vim-Cord act like either Vim or Neovim independently of which one you're actually using:
`g:vim_cord_editor_name` Set it to either `vim` or `nvim`.

You can set a custom tooltip for the RPC's small image:
`g:vim_cord_small_image_tooltip` Set it to any string you want.

## Troubleshooting

- No rpc!
Check that you have all the modules listed in [Dependencies](https://github.com/iosevka-soz/vim-nasm#dependencies).

Run `:UpdateRemotePlugins` if you're on Neovim 

Make sure you have Game Activity enabled on discord.

Make sure you are running Neovim with the same account you installed it. I will not work if you run neovim to edit a file as root only having it installed on your personal account.
