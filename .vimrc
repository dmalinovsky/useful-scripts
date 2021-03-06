set nocompatible              " be iMproved
filetype off                  " required!

set autowrite
set backspace=eol,start,indent " Configure backspace so it acts as it should act
set background=light
set colorcolumn=100
set cursorline
"set diffopt+=iwhite
set expandtab
set fileencodings=ucs-bom,utf-8,default,cp1251
set foldcolumn=1
set foldlevel=2
set foldmethod=indent
set grepprg=ag
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
set number
set shiftwidth=4
set showmatch
set smarttab
set smartcase
set scrolloff=7 " Set 7 lines to the cursor - when moving vertically using j/k
set showbreak=↪
set synmaxcol=600
set tabstop=4
set textwidth=99
set undofile
set undodir=~/.tmp/
set visualbell
set wildignore=*.o,*~,*.pyc,*/lib/*,*/bin/*,*/node_modules/*,*/src/*,*/ve/*,*/uploaded_media/*,*/web-assets/*,*/migrations/*,*/elm-stuff/*
set wildmenu " Turn on the WiLd menu
set whichwrap+=<,>,h,l
set wrap

let g:syntastic_python_checkers=['pyflakes']
let g:syntastic_enable_signs=1
let g:syntastic_error_symbol='✗'
let g:syntastic_warning_symbol='⚠'
let g:syntastic_always_populate_loc_list=1
let g:syntastic_auto_jump=0
let g:syntastic_mode_map = { 'passive_filetypes': ['html'] }

let g:ctrlp_extensions = ['tag', 'buffertag']
let g:ctrlp_max_files = 0

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
Bundle 'ctrlpvim/ctrlp.vim'
Bundle 'jeetsukumaran/vim-buffersaurus'
Bundle 'ElmCast/elm-vim'
Bundle 'ambv/black'

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
" autocmd BufWritePre *.py execute ':Black'
autocmd BufWrite *.coffee :call DeleteTrailingWS()
autocmd BufWrite *.js :call DeleteTrailingWS()
"autocmd BufWrite *.html :call DeleteTrailingWS()

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
nmap <silent> <Leader>d :!open dict://<cword><CR><CR>

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
autocmd BufNewFile,BufRead *.fb2 set syntax=html

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
        execute "grep " . l:pattern
    elseif a:direction == 'f'
        execute "normal /" . l:pattern . "^M"
    endif

    let @/ = l:pattern
    let @" = l:saved_reg
endfunction

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



noremap <F5> <Esc>:syntax sync fromstart<CR>
inoremap <F5> <C-o>:syntax sync fromstart<CR>

" Indent Python in the Google way.

setlocal indentexpr=GetGooglePythonIndent(v:lnum)

let s:maxoff = 50 " maximum number of lines to look backwards.

function GetGooglePythonIndent(lnum)

  " Indent inside parens.
  " Align with the open paren unless it is at the end of the line.
  " E.g.
  "   open_paren_not_at_EOL(100,
  "                         (200,
  "                          300),
  "                         400)
  "   open_paren_at_EOL(
  "       100, 200, 300, 400)
  call cursor(a:lnum, 1)
  let [par_line, par_col] = searchpairpos('(\|{\|\[', '', ')\|}\|\]', 'bW',
        \ "line('.') < " . (a:lnum - s:maxoff) . " ? dummy :"
        \ . " synIDattr(synID(line('.'), col('.'), 1), 'name')"
        \ . " =~ '\\(Comment\\|String\\)$'")
  if par_line > 0
    call cursor(par_line, 1)
    if par_col != col("$") - 1
      return par_col
    endif
  endif

  " Delegate the rest to the original function.
  return GetPythonIndent(a:lnum)

endfunction

let pyindent_nested_paren="&sw*2"
let pyindent_open_paren="&sw*2"
