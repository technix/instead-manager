#!/usr/bin/env python
# -*- coding: UTF-8 -*-

__title__ = 'instead-manager-tk'
__version__ = "0.12"
__author__ = "Evgeniy Efremov aka jhekasoft"
__email__ = "jhekasoft@gmail.com"

import os
from threading import Thread
from tkinter import *
import tkinter.ttk as ttk
import tkinter.font as font
from manager import InsteadManager, WinInsteadManager, InsteadManagerHelper, RepositoryFilesAreMissingError


class InsteadManagerTk(object):
    gui_game_list = {}
    gui_selected_item = ''
    gui_messages = {
        'update_repo': 'Update repositories'
    }

    def __init__(self, instead_manager):
        self.instead_manager = instead_manager

    def begin_repository_downloading_callback(self, repository):
        buttonUpdateRepository['text'] = 'Downloading %s...' % repository['url']

    def end_downloading_repositories(self, list=False):
        buttonUpdateRepository['text'] = self.gui_messages['update_repo']
        buttonUpdateRepository.state(['!disabled'])
        if list:
            self.list_action()

    def list_action(self):
        try:
            game_list = self.instead_manager.get_sorted_combined_game_list()
        except RepositoryFilesAreMissingError:
            return

        gui_repository = comboboxRepository.get()
        gui_lang = comboboxLang.get()

        repositories = [''] + self.instead_manager.get_gamelist_repositories(game_list)
        comboboxRepository['values'] = repositories

        langs = [''] + self.instead_manager.get_gamelist_langs(game_list)
        comboboxLang['values'] = langs

        if gui_keyword.get() or gui_repository or gui_lang:
            game_list = self.instead_manager.filter_games(game_list, gui_keyword.get(), gui_repository, gui_lang)

        # Clear list
        # map(lambda x: print(x), treeRepositoryList.get_children())
        tree_items = treeGameList.get_children()
        for item in tree_items:
            treeGameList.delete(item)

        # Insert games
        self.gui_game_list = {}
        for game in game_list:
            game_list_item = game

            tags = ''
            if game_list_item['installed']:
                tags = 'installed'
            item = treeGameList.insert("", 'end', text=game_list_item['name'], values=(
                game_list_item['title'],
                game_list_item['version'],
                self.instead_manager.size_format(int(game_list_item['size']))
            ), tags=tags)
            self.gui_game_list[item] = game_list_item

    def update_and_list_action(self):
        buttonUpdateRepository.state(['disabled'])
        t = Thread(target=lambda:
                   self.instead_manager.\
                   update_repositories(begin_repository_downloading_callback=self.begin_repository_downloading_callback,
                                       end_downloading_callback=lambda: self.end_downloading_repositories(True)))
        t.start()

    def check_repositories_action(self):
        try:
            self.instead_manager.get_repository_files()
        except RepositoryFilesAreMissingError:
            self.update_and_list_action()
            return
        self.list_action()

    def on_game_list_double_click(self, event):
        #item = treeGameList.identify('item', event.x, event.y)
        item = self.gui_selected_item
        tags = treeGameList.item(item, "tags")

        if 'installed' in tags:
            self.run_game_action()
        else:
            self.install_game_action()


    def download_status_callback(self, item, blocknum, blocksize, totalsize):
        loadedsize = blocknum * blocksize
        if loadedsize > totalsize:
            loadedsize = totalsize

        if totalsize > 0:
            percent = loadedsize * 1e2 / totalsize
            s = "%5.1f%% %s / %s" % (
                percent, self.instead_manager.size_format(loadedsize), self.instead_manager.size_format(totalsize))
            treeGameList.set(item, 'title', '%s %s' % (self.gui_game_list[item]['title'], s))

    def begin_installation_callback(self, item):
        treeGameList.set(item, 'title', '%s installing...' % self.gui_game_list[item]['title'])

    def end_installation(self, item, game, result):
        item_index = treeGameList.index(item)

        self.list_action()

        # Focus installed game
        tree_items = treeGameList.get_children()
        for item in tree_items:
            if treeGameList.index(item) == item_index:
                treeGameList.focus(item)
                treeGameList.selection_set(item)
                treeGameList.yview_scroll(item_index, 'units')
                break

    def on_game_select(self, event):
        self.gui_selected_item = treeGameList.focus()
        title = self.gui_game_list[self.gui_selected_item]['title']
        repository = self.gui_game_list[self.gui_selected_item]['repository_filename']
        version = self.gui_game_list[self.gui_selected_item]['version']
        labelGameTitle.config(text=title)
        labelGameRepository.config(text=repository)
        labelGameVersion.config(text=version)
        self.change_game_buttons_state(self.gui_game_list[self.gui_selected_item]['installed'])

    def install_game_action(self):
        item = self.gui_selected_item

        game = self.gui_game_list[item]

        t = Thread(target=lambda:
            self.instead_manager.install_game(game,
                                              download_status_callback=lambda blocknum, blocksize, totalsize: self.download_status_callback(item, blocknum, blocksize, totalsize),
                                              begin_installation_callback=lambda game: self.begin_installation_callback(item),
                                              end_installation=lambda game, result: self.end_installation(item, game, result)))
        t.start()

    def run_game_action(self):
        item = self.gui_selected_item
        name = treeGameList.item(item, "text")
        self.instead_manager.run_game(name)

    def delete_game_action(self):
        item = self.gui_selected_item
        name = treeGameList.item(item, "text")
        self.instead_manager.delete_game(name)
        self.list_action()

    def change_game_buttons_state(self, installed):
        if installed:
            buttonGamePlay.pack()
            buttonGameDelete.pack()
            buttonGameInstall.pack_forget()
        else:
            buttonGamePlay.pack_forget()
            buttonGameDelete.pack_forget()
            buttonGameInstall.pack()

if __name__ == "__main__":
    base_path = os.path.dirname(os.path.realpath(__file__))

    if InsteadManagerHelper.is_win():
        instead_manager = WinInsteadManager(base_path)
    else:
        instead_manager = InsteadManager(base_path)

    instead_manager_tk = InsteadManagerTk(instead_manager)

    root = Tk(className='INSTEAD Manager')
    root.resizable(width=FALSE, height=FALSE)

    # ttk theme for UNIX-like systems
    if InsteadManagerHelper.is_unix():
        import packages.ttk_themes.plastik.plastik_theme as plastik_theme
        try:
            plastik_theme.install(os.path.join(instead_manager_tk.instead_manager.base_path, 'packages', 'ttk_themes', 'plastik', 'plastik'))
        except Exception:
            import warnings
            warnings.warn("plastik theme being used without images")

    # Window title
    root.title("INSTEAD Manager " + __version__)
    # Window icon
    managerLogo = PhotoImage(file=os.path.join(base_path, 'resources', 'images', 'logo.png'))
    root.iconphoto(True, managerLogo)

    content = ttk.Frame(root, padding=(5, 5, 5, 5))

    frameFilter = ttk.Frame(content, borderwidth=0, relief="flat", width=200, height=100)
    gui_keyword = StringVar()
    def gui_keyword_change(a, b, c):
        instead_manager_tk.list_action()
        entryKeyword.update_idletasks()
    gui_keyword.trace('w', gui_keyword_change)

    def gui_repository_change(widget):
        instead_manager_tk.list_action()

    def gui_lang_change(widget):
        instead_manager_tk.list_action()

    # TODO: move global vars to the GUI class

    # gui_keyword.set('test')
    entryKeyword = ttk.Entry(frameFilter, textvariable=gui_keyword)
    entryKeyword.pack(side=LEFT)

    comboboxRepository = ttk.Combobox(frameFilter, state="readonly")
    comboboxRepository.bind("<<ComboboxSelected>>", gui_repository_change)
    comboboxRepository.pack(side=LEFT, padx=5)

    comboboxLang = ttk.Combobox(frameFilter, state="readonly")
    comboboxLang.bind("<<ComboboxSelected>>", gui_lang_change)
    comboboxLang.pack(side=LEFT)

    frame = ttk.Frame(content, borderwidth=0, relief="flat", width=200, height=100, padding=(5, 0, 0, 0))

    managerLogoFrame = ttk.Button(frame, image=managerLogo)
    labelGameTitle = ttk.Label(frame, text='')
    labelGameRepository = ttk.Label(frame, text='')
    labelGameVersion = ttk.Label(frame, text='')
    buttonGamePlay = ttk.Button(frame, text="Play", command=instead_manager_tk.run_game_action)
    buttonGameDelete = ttk.Button(frame, text="Delete", command=instead_manager_tk.delete_game_action)
    buttonGameInstall = ttk.Button(frame, text="Install", command=instead_manager_tk.install_game_action)

    managerLogoFrame.pack()
    labelGameTitle.pack()
    labelGameRepository.pack()
    labelGameVersion.pack()

    container = ttk.Frame(content, padding=(0, 5, 0, 5))
    #container.pack(fill='both', expand=True)
    treeGameList = ttk.Treeview(container, columns=('title', 'version', 'size'), selectmode='browse', show='headings', height=14)
    treeGameList.column("title", width=350)
    #treeGameList.column("lang", width=50)
    treeGameList.column("version", width=70)
    treeGameList.column("size", width=70)
    #treeGameList.column("repository", width=220)
    treeGameList.heading("title", text="Title")
    #treeGameList.heading("lang", text="Lang", command=lambda: print('lang'))
    treeGameList.heading("version", text="Version")
    treeGameList.heading("size", text="Size")
    #treeGameList.heading("repository", text="Repository")
    # installed_font = font.Font(font=labelGameTitle.cget("font")).copy()
    # installed_font.config(weight=font.BOLD)
    treeGameList.tag_configure('installed', background='#f0f0f0')
    treeGameList.bind("<Double-1>", instead_manager_tk.on_game_list_double_click)
    treeGameList.bind('<<TreeviewSelect>>', instead_manager_tk.on_game_select)
    vsb = ttk.Scrollbar(orient="vertical", command=treeGameList.yview)
    treeGameList.configure(yscrollcommand=vsb.set)
    treeGameList.grid(column=0, row=0, sticky=(N, S, E, W))
    vsb.grid(column=1, row=0, sticky='ns', in_=container)
    container.grid_columnconfigure(0, weight=1)
    container.grid_rowconfigure(0, weight=1)

    buttonUpdateRepository = ttk.Button(content, text=instead_manager_tk.gui_messages['update_repo'], command=instead_manager_tk.update_and_list_action, width=40)

    content.pack(fill='both', expand=True)
    frameFilter.grid(column=0, row=0, sticky=(N, S, E, W))
    container.grid(column=0, row=1, columnspan=3, rowspan=1, sticky=(N, S, E, W))
    frame.grid(column=4, row=0, columnspan=3, rowspan=2, sticky=(N, S, E, W))
    buttonUpdateRepository.grid(column=0, row=3, sticky=(N, S, E, W))

    root.wait_visibility()
    instead_manager_tk.check_repositories_action()
    root.mainloop()
