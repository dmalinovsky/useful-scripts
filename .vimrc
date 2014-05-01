set nocompatible              " be iMproved
filetype off                  " required!

set autowrite
set backspace=eol,start,indent " Configure backspace so it acts as it should act
set background=light
set colorcolumn=80
set cursorline
set diffopt+=iwhite
set expandtab
set foldcolumn=1
set foldlevel=2
set foldmethod=indent
set grepprg=ack
set guifont=Menlo\ Regular:h14
set history=700 " Sets how many lines of history VIM has to remember
set hlsearch
set ignorecase " Ignore case when searching
set incsearch
set laststatus=2
set lazyredraw
set linebreak
set magic
set mouse=a
set relativenumber
set shiftwidth=4
set showmatch
set smarttab
set smartcase
set scrolloff=7 " Set 7 lines to the cursor - when moving vertically using j/k
set showbreak=↪
set synmaxcol=600
set tabstop=4
set textwidth=79
set undofile
set undodir=~/.tmp/
set visualbell
set wildignore=*.o,*~,*.pyc,lib/*,bin/*,node_modules/*,src/*
set wildmenu " Turn on the WiLd menu
set whichwrap+=<,>,h,l
set wrap

let g:syntastic_python_checkers=['pyflakes']
let g:syntastic_enable_signs=1
let g:syntastic_error_symbol='✗'
let g:syntastic_warning_symbol='⚠'
let g:syntastic_always_populate_loc_list=1
let g:syntastic_auto_jump=0

let g:ctrlp_extensions = ['tag', 'buffertag']

set rtp+=~/.vim/bundle/vundle/
call vundle#rc()

" let Vundle manage Vundle
" required!
Bundle 'gmarik/vundle'

Bundle 'bling/vim-airline'
Bundle 'scrooloose/nerdtree'
Bundle 'scrooloose/syntastic'
Bundle 'tpope/vim-fugitive'
Bundle 'rizzatti/funcoo.vim'
Bundle 'rizzatti/dash.vim'
Bundle 'kien/ctrlp.vim'
" non-GitHub repos
"Bundle 'git://git.wincent.com/command-t.git'

filetype plugin indent on     " required!

syntax on

map <silent> <space> :noh<cr>

" Return to last edit position when opening files (You want this!)
autocmd BufReadPost *
     \ if line("'\"") > 0 && line("'\"") <= line("$") |
     \   exe "normal! g`\"" |
     \ endif

let python_highlight_all = 1
au FileType python syn keyword pythonDecorator True None False self

" Delete trailing white space on save, useful for Python and CoffeeScript ;)
func! DeleteTrailingWS()
  exe "normal mz"
  %s/\s\+$//ge
  exe "normal `z"
endfunc
autocmd BufWrite *.py :call DeleteTrailingWS()
autocmd BufWrite *.coffee :call DeleteTrailingWS()
autocmd BufWrite *.js :call DeleteTrailingWS()
autocmd BufWrite *.html :call DeleteTrailingWS()

" Keep search matches in the middle of the window.
nnoremap * *zzzv
nnoremap # #zzzv
nnoremap n nzzzv
nnoremap N Nzzzv

" Use the arrows to something usefull
map <right> :bn<cr>
map <left> :bp<cr>

nnoremap <leader>k :NERDTreeFind<cr>
nnoremap <leader>n :NERDTreeToggle<cr>

nnoremap <leader>t :CtrlPTag<CR>
nnoremap <leader>a :CtrlPBufTagAll<CR>

nnoremap <leader>c :cn<CR>zO

nnoremap <leader>b :CtrlPBuffer<CR>

nmap <silent> <leader>d <Plug>DashSearch

fun! DetectTemplate()
  let n = 1
  while n < line("$")
    if getline(n) =~ '{%' || getline(n) =~ '{{'
      set ft=htmldjango
      return
    endif
    let n = n + 1
  endwhile
  "set ft=html "default html
endfun

autocmd BufNewFile,BufRead *.html call DetectTemplate()
autocmd BufNewFile,BufRead *.xml call DetectTemplate()

""""""""""""""""""""""""""""""
" => Visual mode related
""""""""""""""""""""""""""""""
" Really useful!
"  In visual mode when you press * or # to search for the current selection
vnoremap <silent> * :call VisualSearch('f')<CR>
vnoremap <silent> # :call VisualSearch('b')<CR>

" When you press gv you vimgrep after the selected text
vnoremap <silent> gv :call VisualSearch('gv')<CR>
"map <leader>g :vimgrep // **/*<left><left><left><left><left><left><left>


function! CmdLine(str)
    exe "menu Foo.Bar :" . a:str
    emenu Foo.Bar
    unmenu Foo
endfunction

" From an idea by Michael Naumann
function! VisualSearch(direction) range
    let l:saved_reg = @"
    execute "normal! vgvy"

    let l:pattern = escape(@", '\\/.*$^~[]')
    let l:pattern = substitute(l:pattern, "\n$", "", "")

    if a:direction == 'b'
        execute "normal ?" . l:pattern . "^M"
    elseif a:direction == 'gv'
        call CmdLine("grep " . l:pattern)
    elseif a:direction == 'f'
        execute "normal /" . l:pattern . "^M"
    endif

    let @/ = l:pattern
    let @" = l:saved_reg
endfunction

autocmd BufEnter * :syntax sync fromstart
noremap <F12> <Esc>:syntax sync fromstart<CR>
inoremap <F12> <C-o>:syntax sync fromstart<CR>
