#!/usr/bin/env python
# -*- coding: UTF-8 -*-

__title__ = 'instead-manager'
__version__ = "0.8"
__author__ = "Evgeniy Efremov aka jhekasoft"
__email__ = "jhekasoft@gmail.com"

import os
from threading import Thread
from tkinter import *
import tkinter.ttk as ttk
from manager import InsteadManager, WinInsteadManager, InsteadManagerHelper


class InsteadManagerTk(object):
    gui_game_list = {}
    gui_selected_item = ''

    def __init__(self, instead_manager):
        self.instead_manager = instead_manager

    def begin_repository_downloading_callback(self, repository):
        print('Downloading %s...' % repository['url'])

    def update_repositories_action(self):
        self.instead_manager.\
            update_repositories(begin_repository_downloading_callback=self.begin_repository_downloading_callback)

    def list_action(self):
        game_list = self.instead_manager.get_sorted_game_list()

        local_game_list = self.instead_manager.get_sorted_local_game_list()

        local_game_names = []
        for local_game in local_game_list:
            local_game_names.append(local_game['name'])

        # Clear list
        # map(lambda x: print(x), treeRepositoryList.get_children())
        tree_items = treeGameList.get_children()
        for item in tree_items:
            treeGameList.delete(item)

        # Insert games
        self.gui_game_list = {}
        for game in game_list:
            game_list_item = game
            game_list_item['installed'] = True if game['name'] in local_game_names else False

            tags = ''
            if game_list_item['installed']:
                tags = 'installed'
            item = treeGameList.insert("", 'end', text=game_list_item['name'], values=(
                game_list_item['title'],
                game_list_item['lang'],
                game_list_item['version'],
                self.instead_manager.size_format(int(game_list_item['size'])),
                game_list_item['repository_filename']
            ), tags=tags)
            self.gui_game_list[item] = game_list_item

    def update_and_list_action(self):
        self.update_repositories_action()
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
        # tags = treeGameList.item(item, "tags")
        name = treeGameList.item(item, "text")
        title = treeGameList.item(item, "values")[0]

        game_list = self.instead_manager.get_sorted_game_list()
        filtered_game_list = self.instead_manager.filter_games(game_list, name)

        # found = bool(filtered_game_list)
        for game in filtered_game_list:

            t = Thread(target=lambda:
                self.instead_manager.install_game(game,
                                                  download_status_callback=lambda blocknum, blocksize, totalsize: self.download_status_callback(item, blocknum, blocksize, totalsize),
                                                  begin_installation_callback=lambda game: self.begin_installation_callback(item),
                                                  end_installation=lambda game, result: self.end_installation(item, game, result)))
            t.start()

            break

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
            buttonGamePlay.state(['!disabled'])
            buttonGameDelete.state(['!disabled'])
            buttonGameInstall.state(['disabled'])
        else:
            buttonGamePlay.state(['disabled'])
            buttonGameDelete.state(['disabled'])
            buttonGameInstall.state(['!disabled'])

if __name__ == "__main__":
    base_path = os.path.dirname(os.path.realpath(__file__))

    if InsteadManagerHelper.is_win():
        instead_manager = WinInsteadManager(base_path)
    else:
        instead_manager = InsteadManager(base_path)

    instead_manager_tk = InsteadManagerTk(instead_manager)

    root = Tk(className='INSTEAD Manager')
    # Window title
    root.title("INSTEAD Manager " + __version__)
    # Window icon
    root.iconphoto(True, PhotoImage(file=os.path.join(base_path, 'resources', 'images', 'logo.png')))

    # style = ttk.Style()
    # print(style.theme_names())
    # style.theme_use('clam')

    content = ttk.Frame(root)
    frame = ttk.Frame(content, borderwidth=5, relief="sunken", width=200, height=100)

    labelGameTitle = ttk.Label(frame, text='')
    labelGameRepository = ttk.Label(frame, text='')
    labelGameVersion = ttk.Label(frame, text='')
    buttonGamePlay = ttk.Button(frame, text="Play", state="disabled", command=instead_manager_tk.run_game_action)
    buttonGameDelete = ttk.Button(frame, text="Delete", state="disabled", command=instead_manager_tk.delete_game_action)
    buttonGameInstall = ttk.Button(frame, text="Install", state="disabled", command=instead_manager_tk.install_game_action)

    labelGameTitle.pack()
    labelGameRepository.pack()
    labelGameVersion.pack()
    buttonGamePlay.pack()
    buttonGameDelete.pack()
    buttonGameInstall.pack()

    treeGameList = ttk.Treeview(content, columns=('title', 'lang', 'version', 'size', 'repository'), show='headings')
    treeGameList.column("title", width=350)
    treeGameList.column("lang", width=50)
    treeGameList.column("version", width=70)
    treeGameList.column("size", width=70)
    treeGameList.column("repository", width=220)
    treeGameList.heading("title", text="Title")
    treeGameList.heading("lang", text="Lang", command=lambda: print('lang'))
    treeGameList.heading("version", text="Version")
    treeGameList.heading("size", text="Size")
    treeGameList.heading("repository", text="Repository")
    treeGameList.tag_configure('installed', background='#dfd')
    treeGameList.bind("<Double-1>", instead_manager_tk.on_game_list_double_click)
    treeGameList.bind('<<TreeviewSelect>>', instead_manager_tk.on_game_select)
    # treeGameList.pack()

    buttonUpdateRepository = ttk.Button(content, text="Update repositories", command=instead_manager_tk.update_and_list_action)

    content.grid(column=0, row=0)
    treeGameList.grid(column=0, row=0, columnspan=3, rowspan=2)
    frame.grid(column=4, row=0, columnspan=3, rowspan=2)
    buttonUpdateRepository.grid(column=0, row=3)

    # Style Sheet
    # s = ttk.Style()
    # s.configure('TFrame', background='#5555ff')
    # s.configure('TButton', background='blue', foreground='#eeeeff', font=('Sans', '14', 'bold'), sticky=EW)
    # s.configure('TLabel', font=('Sans', '16', 'bold'), background='#5555ff', foreground='#eeeeff')
    # s.map('TButton', foreground=[('hover', '#5555ff'), ('focus', 'yellow')])
    # s.map('TButton', background=[('hover', '#eeeeff'), ('focus', 'orange')])
    # s.configure('TCombobox', background='#5555ff', foreground='#3333ff', font=('Sans', 18))

    #buttonUpdateRepository.pack()

    instead_manager_tk.list_action()
    root.mainloop()
