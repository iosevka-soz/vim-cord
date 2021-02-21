# Vim-Cord

Quick and simple, single file Discord RPC integration for Neovim. (And soon Vim)

# Installation

[Pathogen](https://github.com/tpope/vim-pathogen)
    `git clone https://github.com/iosevka-soz/vim-cord` into your installation's Bundle directory.

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
`g:loaded_vim_cord` Set it to anything to disable vim-cord.

You can make vim-cord show up on discord as:
- vi
- vim
- neovim
- gvim
- macvim
`g:vim_cord_editor_override` Set it to any of the above to lock Vim-Cord to show up on discord as it.

`g:vim_cord_app_id_override` You can set this to add a custom discord app with your own icons and use that for vim-cord, if you set this, it will be locked to it, so `g:vim_cord_editor_override` will be effectively ignored.

`g:vim_cord_<EDITOR_NAME>_app_id` This can be used to give a custom discord app id to each of the built-in supported editors, for example:
`let g:vim_cord_vim_app_id = 836288358629062416` will make Vim-cord use "836288358629062416" as the discord app id if it determines vim is the editor in use either by override or by detecting the environment.
This can be used for any of the supported editors by replacing EDITOR_NAME with the actual name.

`g:vim_cord_discord_retry` (Default: 1) If set to 1, Vim-Cord will try to reconnect to discord <`g:vim_cord_max_retry`> times if it fails. By default that is 3 times.

`g:vim_cord_max_retry` (default: 3) This is how many times Vim-Cord will attempt to reconnect to the discord RPC server, it only makes sense if `g:vim_cord_discord_retry` is set to 1.

`g:vim_cord_discord_retry_delay` (default: 10) This is how much time in SECONDS Vim-Cord will wait in between each connection retry, only makes sense if `g:vim_cord_discord_retry` is set to 1.

`g:vim_cord_track_modifiable` (default: 1) Wether Vim-Cord should track wether the current buffer is modifiable or not, this will change prefixes from "Editing" to "Reading" depending on that in the RPC.

## Commands
`VimCordReconnect` Use it to force a reconnection retry at anytime, parameters for this are defined the same as the initial connection attempts.

## Troubleshooting

- No rpc!
Check that you have all the modules listed in [Dependencies](https://github.com/iosevka-soz/vim-nasm#dependencies).

Run `:UpdateRemotePlugins` if you're on Neovim 

Make sure you have Game Activity enabled on discord.

Make sure you are running Neovim with the same account you installed it. It will not work if you run neovim to edit a file as root only having it installed on user account for example.

## TODO
Fix discord connection retry blocking vim exit.
