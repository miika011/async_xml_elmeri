import tkinter
from tkinter import ttk
import tkinter.filedialog
import tkinter.messagebox
import os
import glob
import configparser
import xml.etree.ElementTree as ETree
from collections import defaultdict
import asyncio
import concurrent.futures
from threading import Thread
import concurrent.futures

# Separate thread to run parsing if needed
xmlParseThread = asyncio.new_event_loop()
def f(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

t = Thread(target=f, args=(xmlParseThread,))
t.start()

def getScriptDirectory() -> str:
    return os.path.dirname(os.path.abspath(__file__))

class XPathModifierGUI:
    WINDOW_NAME = "XPath Modifier (7 Days to Die)"
    CONFIG_FILE_NAME = "XPath.ini"
    CONFIG_SECTION_NAME = "Settings"
    CONFIG_OPTION_NAME_GAME_ROOT = "xmlFolderPath"
    CONFIG_OPTION_NAME_WINDOWSIZE = "windowSize"
    CONFIG_OPTION_NAME_LEFTPANEWIDTH = "leftPaneWidth"
    CONFIG_OPTION_NAME_RIGHTPANEWIDTH = "rightPaneWidth"

    DEFAULT_WINDOW_SIZE = "900x600"
    DEFAULT_LEFT_PANE_WIDTH = "650"
    DEFAULT_RIGHT_PANE_WIDTH = "250"

    def __init__(self):
        self.running = False
        self.loadConfigs()
        
        self.root = tkinter.Tk()
        self.topMenu = TopMenu(root=self.root, 
                               onSelectConfigFolder=self.saveGameFolder, 
                               onQuit=self.quit,
                               onSelectOutputFolder=self.onSelectOutputFolder,
                               onWriteChanges=self.onWriteChanges)
        self.root.config(menu=self.topMenu.menuBar)
        
        
        self.panedWindow = tkinter.PanedWindow(self.root, orient=tkinter.HORIZONTAL)
        self.leftFrame = tkinter.Frame(self.panedWindow, )
        self.rightFrame = tkinter.Frame(self.panedWindow, )
        self.fileView = FileView(master=self.leftFrame, headerText="XML Files:")
        self.changesView = ChangesView(master=self.rightFrame)

        self.panedWindow.add(self.leftFrame,stretch="always")
        self.panedWindow.add(self.rightFrame, )
        self.panedWindow.pack()

        self.updateLayout()
        self.updateTitle(self.getSavedFolder())

        self.root.protocol("WM_DELETE_WINDOW", self.quit)
        self.root.geometry(self.getSavedWindowSize())
        self.setFrameWidths(leftFrameWidth=self.getSavedLeftFrameWidth(), rightFrameWidth=self.getSavedRightFrameWidth())
        
        

    def updateTitle(self, newFolder) -> None:
        if not newFolder:
            title = XPathModifierGUI.WINDOW_NAME
        else:
            title = f"{XPathModifierGUI.WINDOW_NAME} - {newFolder}"
        self.root.title(title)

    def getSavedRightFrameWidth(self) -> str:
        return self.getConfig(name=XPathModifierGUI.CONFIG_OPTION_NAME_RIGHTPANEWIDTH, defaultValue=XPathModifierGUI.DEFAULT_RIGHT_PANE_WIDTH)

    def getSavedLeftFrameWidth(self) -> str:
        return self.getConfig(name=XPathModifierGUI.CONFIG_OPTION_NAME_LEFTPANEWIDTH, defaultValue=XPathModifierGUI.DEFAULT_LEFT_PANE_WIDTH)

    def getSavedFolder(self) -> str:
        return self.getConfig(name=XPathModifierGUI.CONFIG_OPTION_NAME_GAME_ROOT, defaultValue="")
        
    def getSavedWindowSize(self) -> str:
        return self.getConfig(name=XPathModifierGUI.CONFIG_OPTION_NAME_WINDOWSIZE, defaultValue=XPathModifierGUI.DEFAULT_WINDOW_SIZE)

    def getConfig(self,*,name, defaultValue) -> str:
        try:
            return self.configs.get(section=XPathModifierGUI.CONFIG_SECTION_NAME, option=name)
        except:
            return defaultValue
        
    def setConfig(self, *, name, value) -> None:
        try:
            self.configs.set(section=XPathModifierGUI.CONFIG_SECTION_NAME, option=name, value=value)
        except:
            return

    def updateLayout(self) -> None:        
        self.panedWindow.paneconfigure(self.rightFrame)
        self.panedWindow.paneconfigure(self.leftFrame)
        self.panedWindow.pack(fill=tkinter.BOTH, expand=True)
        
    def setFrameWidths(self,*,leftFrameWidth = None, rightFrameWidth = None) -> None:
        self.panedWindow.paneconfigure(self.leftFrame,width=leftFrameWidth)
        self.panedWindow.paneconfigure(self.rightFrame,width=rightFrameWidth)



    def updateConfigsWindowSize(self, width, height) -> None:
        size = f"{width}x{height}"
     
        self.setConfig(
            name=XPathModifierGUI.CONFIG_OPTION_NAME_WINDOWSIZE, 
            value=size)

    def initBindings(self) -> None:
      self.root.bind("<<Saved>>", lambda e: self.updateState())
        
    def start(self):
        self.initBindings()
        self.running = True
        savedGameFolder = self.getConfig(name=XPathModifierGUI.CONFIG_OPTION_NAME_GAME_ROOT, defaultValue="")
        if (savedGameFolder):
            self.root.event_generate("<<Saved>>")
        self.root.mainloop()


    def updateState(self) -> None:
        folder = self.getConfig(name=XPathModifierGUI.CONFIG_OPTION_NAME_GAME_ROOT, defaultValue="")
        folder = os.path.abspath(folder)
        if not isReadableFolder(folder):
            tkinter.messagebox.showerror("No read permission",f"You don't have read permissions for \"{folder}\"")
        self.updateTitle(folder)
        self.fileView.setGameRootFolder(folder)

    def onSelectOutputFolder(self, folderStr) -> None:
        if not isWriteableFolder(folderStr):
            self.showErrorNotWriteable(folderStr)
        self.outputFolder = folderStr
        self.topMenu.enableWriteChangesItem()

    def showErrorNotWriteable(self, path) -> None:
        tkinter.messagebox.showerror("No write permission",f"You don't have write permissions for \"{path}\"")

    def onWriteChanges(self):
        pass

    def saveGameFolder(self, folder) -> None:
        self.setConfig(name=XPathModifierGUI.CONFIG_OPTION_NAME_GAME_ROOT,value=folder)
        print("Saving!")
        self.root.event_generate("<<Saved>>")

    def loadConfigs(self) -> None:
        configPath = self.getConfigFilePath()
        self.configs = configparser.ConfigParser()
        if os.access(configPath,os.R_OK):
            self.configs.read(configPath)
            
        for (option, defaultValue) in (
            (XPathModifierGUI.CONFIG_OPTION_NAME_GAME_ROOT, ""),
            (XPathModifierGUI.CONFIG_OPTION_NAME_WINDOWSIZE, XPathModifierGUI.DEFAULT_WINDOW_SIZE), 
            (XPathModifierGUI.CONFIG_OPTION_NAME_LEFTPANEWIDTH, XPathModifierGUI.DEFAULT_LEFT_PANE_WIDTH),
            (XPathModifierGUI.CONFIG_OPTION_NAME_RIGHTPANEWIDTH, XPathModifierGUI.DEFAULT_RIGHT_PANE_WIDTH)
        ):
            self._configSetDefaultsIfNotPresent(section=XPathModifierGUI.CONFIG_SECTION_NAME,
                option=option, 
                defaultValue=defaultValue
            )


    def _configSetDefaultsIfNotPresent(self, *, section, option, defaultValue) -> None:
        if not self.configs.has_section(section):
            self.configs.add_section(section)

        if not self.configs.has_option(section=section, option=option):
            self.configs.set(section=section, option=option, value=defaultValue)

    def getConfigFilePath(self) -> None:
        return os.path.join(getScriptDirectory(), XPathModifierGUI.CONFIG_FILE_NAME)

    def writeConfigs(self) -> None:
        configPath = self.getConfigFilePath()
        with open(configPath, "w") as file:
            self.configs.write(file)

    def quit(self) -> None:
        self.updateConfigsWindowSize(self.root.winfo_width(), self.root.winfo_height())

        self.setConfig(name=XPathModifierGUI.CONFIG_OPTION_NAME_LEFTPANEWIDTH, 
                        value=str(self.leftFrame.winfo_width())
        )
        self.setConfig(name=XPathModifierGUI.CONFIG_OPTION_NAME_RIGHTPANEWIDTH,
                         value=str(self.rightFrame.winfo_width())
        )

        self.writeConfigs()
        self.running= False

class XmlTagParams:
  def __init__(self, element: ETree.Element, rowParent: str, filePath: str, xPath: str, childCounts = None):
    self.element = element
    self.rowParent = rowParent
    self.filePath = filePath
    self.xPath = xPath
    self.childCounts = childCounts

class FileView:
    #Class variables and functions
    TAG_FOLDER_ROW = "folder"
    COLOR_FOLDER_ROW = "#f4f4f4"
    TAG_FILE = "file"
    COLOR_FILE_ROW = "#f4f4f4"
    TAG_TAG_ROW = "tag"
    COLOR_TAG_ROW = "#f4f4f4"
    TAG_ATTRIBUTE_ROW = "attribute"
    COLOR_ATTRIBUTE_ROW = "#f4f4f4"

    MAX_DEPTH_XML_RECURSE = 10
    MAX_DEPTH_FOLDER_RECURSE = 10 #To prevent overflow in case for some reason we have a link pointing to the same folder tree
    
    PATH_RELATIVE_CONFIG_FOLDER = os.path.join("Data", "Config")

    #Instance functions
    def __init__(self, *, master, headerText, configFolder=""):
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self.itemIdToXmlModification = dict()
        self.configFolder = configFolder
        self.headerText = headerText
        self.tree = ttk.Treeview(master=master,selectmode=tkinter.BROWSE) #selectmode="brose" means single select items
        self.configureTags()
        self.tree.pack(fill=tkinter.BOTH,expand=True)
        self.tree.heading("#0", text=self.headerText)
        self.scrollbar = tkinter.Scrollbar(self.tree, orient=tkinter.VERTICAL, command=self.tree.yview)
        self.scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        self.tree.configure(yscrollcommand=self.scrollbar.set)


    def configureTags(self) -> None:
        self.tree.tag_configure(FileView.TAG_FILE, background=FileView.COLOR_FILE_ROW)
        self.tree.tag_configure(FileView.TAG_FOLDER_ROW, background=FileView.COLOR_FOLDER_ROW)
        self.tree.tag_configure(FileView.TAG_TAG_ROW, background=FileView.COLOR_TAG_ROW)
        self.tree.tag_configure(FileView.TAG_ATTRIBUTE_ROW, background=FileView.COLOR_ATTRIBUTE_ROW)
        #Button 3: right mouse
        self.tree.tag_bind(FileView.TAG_TAG_ROW, sequence="<ButtonRelease-3>", callback=lambda event: self.onOpenMenu(event))
        self.tree.tag_bind(FileView.TAG_TAG_ROW, sequence="<Button-3>", callback=lambda event: self.onSelectItem(event))

    def setGameRootFolder(self, folderPath) -> None:
        configFolder = os.path.join(folderPath,FileView.PATH_RELATIVE_CONFIG_FOLDER)
        if not isReadableFolder(configFolder):
            return
        self.clear()
        self.configFolder = configFolder
        self._addFolder(self.configFolder)



    
    def _addFolder(self, folderPath, *, depth = 0) -> None:
        print(f"adding {folderPath}")
        if depth > FileView.MAX_DEPTH_FOLDER_RECURSE:
            return
        parent = self.tree.insert("",tkinter.END,text=folderPath,tags=(FileView.TAG_FOLDER_ROW,))
        xmlFiles = glob.glob(os.path.join(folderPath, "*.xml"))
        for xmlFilePath in xmlFiles:
            self._addFile(xmlFilePath, parent=parent)
        
        for subFolder in map(lambda subFolder: os.path.join(folderPath,subFolder),os.listdir(folderPath)):
            if os.path.isdir(subFolder):
                self._addFolder(os.path.join(folderPath,subFolder),depth=depth+1)
    

    def _addFile(self, filePath, *, parent="") -> None:
        print(f"adding {filePath}")
        fileRow = self.tree.insert(parent, tkinter.END, tags=(FileView.TAG_FILE,), text=os.path.basename(filePath))
        try:
            xmlParsed = ETree.parse(filePath)
            xmlRoot = xmlParsed.getroot()
            # Comment this if you want asynchronous
            self._addXmlTag(element=xmlRoot, xPath=f"/{xmlRoot.tag}", rowParent=fileRow, filePath = filePath)
            # Uncomment this if you want asynchronous
            # future = asyncio.run_coroutine_threadsafe(self._addXmlTagAsync(element=xmlRoot, xPath=f"/{xmlRoot.tag}", rowParent=fileRow, filePath = filePath), xmlParseThread)
        except Exception as e:
            return

    def _addXmlTag(self, *, element: ETree.Element, rowParent: str, filePath: str, xPath: str, depth=0, childCounts = None) -> None:
        stack = []
        rootParams = XmlTagParams(element, rowParent, filePath, xPath, childCounts)
        stack.append(rootParams)
        while(len(stack) > 0):
            node = stack.pop()
            _childCounts = node.childCounts or ChildCounts()
            subFolder = os.path.relpath(os.path.dirname(node.filePath), start=self.configFolder)
            self._addModification(treeItemID=node.rowParent,xmlModification= XmlModification(element=node.element, xPath=node.xPath, subFolder=subFolder))

            for attributeName, attributeValue in node.element.attrib.items():
                attributeListItem = self.tree.insert(node.rowParent, tkinter.END, tags= (FileView.TAG_ATTRIBUTE_ROW,), text=f"{attributeName}: {attributeValue}")
                self._addModification(treeItemID=attributeListItem, xmlModification= XmlModification(element=node.element, xPath= f"{node.xPath}[@{attributeName}]", subFolder=subFolder))

            for child in iter(node.element):
                nextParent = self.tree.insert(node.rowParent, tkinter.END, tags=(FileView.TAG_TAG_ROW), text=f"<{child.tag}>")
                childXPath = self.buildXPath(parentsXPath=node.xPath, child=child, childCounts=_childCounts)
                childNode = XmlTagParams(element=child, xPath=childXPath, rowParent=nextParent, filePath=filePath, childCounts=_childCounts)
                stack.append(childNode)

    async def _addXmlTagAsync(self, *, element: ETree.Element, rowParent: str, filePath: str, xPath: str, depth=0, childCounts = None) -> None:
        stack = []
        rootParams = XmlTagParams(element, rowParent, filePath, xPath, childCounts)
        stack.append(rootParams)
        while(len(stack) > 0):
            node = stack.pop()
            _childCounts = node.childCounts or ChildCounts()
            subFolder = os.path.relpath(os.path.dirname(node.filePath), start=self.configFolder)
            self._addModification(treeItemID=node.rowParent,xmlModification= XmlModification(element=node.element, xPath=node.xPath, subFolder=subFolder))

            for attributeName, attributeValue in node.element.attrib.items():
                attributeListItem = self.tree.insert(node.rowParent, tkinter.END, tags= (FileView.TAG_ATTRIBUTE_ROW,), text=f"{attributeName}: {attributeValue}")
                self._addModification(treeItemID=attributeListItem, xmlModification= XmlModification(element=node.element, xPath= f"{node.xPath}[@{attributeName}]", subFolder=subFolder))

            for child in iter(node.element):
                nextParent = self.tree.insert(node.rowParent, tkinter.END, tags=(FileView.TAG_TAG_ROW), text=f"<{child.tag}>")
                childXPath = self.buildXPath(parentsXPath=node.xPath, child=child, childCounts=_childCounts)
                childNode = XmlTagParams(element=child, xPath=childXPath, rowParent=nextParent, filePath=filePath, childCounts=_childCounts)
                stack.append(childNode)


    def buildXPath(self,* , parentsXPath, child, childCounts ):
        baseXPath = f"{parentsXPath}/{child.tag}"
        childIndex = childCounts.getNextIndex(baseXPath)
        childCounts.increment(baseXPath)
        return baseXPath + f"[{childIndex}]"

    def _addModification(self,*, treeItemID,xmlModification) -> None:
        self.itemIdToXmlModification[treeItemID] = xmlModification

    def clear(self) -> None:
        self.itemIdToXmlModification.clear()
        self.tree.delete(*self.tree.get_children())

    def onOpenMenu(self, event) -> None:
        #sel =self.tree.selection_get()
        selections = self.tree.selection()
        if not selections:
            return
        itemId = selections[0]
        print(itemId)
        t = self.itemIdToXmlModification[itemId]
        print(t.xPath)
        contextMenu = tkinter.Menu(self.tree, tearoff=0)
        contextMenu.add_command(label="kakka")
        contextMenu.add_command(label="kököö")
        contextMenu.post(event.x_root, event.y_root)

    def onSelectItem(self, event) -> None:
        itemId = self.tree.identify_row(event.y)
        self.tree.selection_set(itemId)

class ChildCounts:
    def __init__(self) -> None:
        self._defaultDict = defaultdict(lambda: 1)
    def getNextIndex(self, xPath: str):
        return self._defaultDict[xPath]
    def increment(self, xPath: str):
        self._defaultDict[xPath] += 1

class XmlModification:
    def __init__(self, *, element:ETree.Element, xPath, attributeChanges = dict(), contentChange = "", subFolder = ""):
        self.originalAttributes = dict(element.items())
        self.xPath = xPath
        self.attributeChanges = attributeChanges
        self.contentChange = contentChange
        self.subFolder = subFolder

class ChangesView:
    ATTRIBUTE_VALUE_INDEX = 1

    def __init__(self,master: tkinter.Widget,*, outputFolder = ""):
        self.master = master
        self.highlightBox = None
        self.label = tkinter.Label(master=master,height=1,text="Details:")
        self.label.pack(expand=False, fill="x",)
        
        self.tree = ttk.Treeview(master=master,columns=("attribute","value"),show="headings", selectmode= "none")
        self.tree.heading("attribute", text="Attribute")
        self.tree.heading("value", text="Value")
        # self.tree.pack(expand=True, fill="both")
        # self.outputFolder = outputFolder
        # self.tree.insert("",0,values=("attribute1", "value1"),tags=("data_row"))
        # self.tree.insert("",1,values=("attribute2", "value2"),tags=("data_row"))
        
        self.tree.tag_bind("data_row", "<Double-1>", self.onClick)

    def getHeadingText(self) -> str:
        return "Changes done:"
    
    def onClick(self, event: tkinter.Event):
        column = self.tree.identify_column(event.x)
        if column != "#2":
            return
        row = self.tree.identify_row(event.y)
        self.highlight(column, row)

    def highlight(self, column, row):
        x,y,width,height = self.tree.bbox(row, column=column)
        oldValue = str(self.tree.item(row)["values"][ChangesView.ATTRIBUTE_VALUE_INDEX]) #str() is needed because if the attribute is a number, it is stored as a numeric type instead of string.

        self.highlightBox and self.highlightBox.destroy()
        self.highlightBox = tkinter.Text(master=self.tree,height=1)
        self.highlightBox.config(endline="")
        self.highlightBox.insert("1.0", oldValue)
        self.highlightBox.place(x=x, y=y, width=width, height=height)
        self.highlightBox.focus()

        #note to self: "sel" is a predefined tag that handles text selection
        #also text indexes are strings "line.chrIndex" where lines start from 1, chrIndex starts from 0 just as indices on strings
        self.highlightBox.tag_add("sel", "1.0", f"1.{len(oldValue)}") 
        self.highlightBox.bind("<Return>", lambda e: self.onPressedEnter( column=column, row=row))
        self.highlightBox.bind("<Tab>", lambda e: self.onPressedTab( column=column, row=row))
        self.highlightBox.bind("<Escape>", lambda e: self.onPressedEscape( column=column, row=row))
        self.highlightBox.bind("<FocusOut>", lambda e: self.onPressedEscape( column=column, row=row))

    def onPressedEnter(self, *, column: str, row: str):
        if not self.highlightBox:
            return

        #note to self: "-1c" means "subtract one character"
        #"-1c" to soak the newline at the end:
        self.tree.set(row, column=column, value=self.highlightBox.get("1.0","end-1c"))
        self.highlightBox.destroy()
        return "break"
    
    def onPressedTab(self,  *,column: str, row: str):
        allRows = self.tree.get_children()
        thisIndex = allRows.index(row)
        self.onPressedEnter( column=column, row= row)
        self.highlight(column=column, row=allRows[(thisIndex+1)%len(allRows)])

        print(f"column: {column}")
        print(f"row: {row}")
        print(f"children: {allRows}")
        return "break"

    def onPressedEscape(self, *, column: str, row: str):
        self.highlightBox and self.highlightBox.destroy()
        return "break"


        

class TopMenu:
    LABEL_SELECT_GAME_FOLDER = "Select game folder"
    LABEL_SELECT_OUTPUT_FOLDER = "Select output folder"
    LABEL_WRITE_CHANGES = "Write changes to output folder"
    LABEL_EXIT = "Exit"

    def __init__(self, *,root:tkinter.Tk, onSelectConfigFolder, onSelectOutputFolder, onWriteChanges, onQuit = lambda: None):
        self.onSelectConfigFolder = onSelectConfigFolder
        self.onSelectOutputFolder = onSelectOutputFolder
        self.onWriteChanges = onWriteChanges
        self.onQuit = onQuit
        self.menuBar = tkinter.Menu(root)
        
        self.fileMenu = tkinter.Menu(self.menuBar,tearoff=False)
        self.fileMenu.add_command(label=TopMenu.LABEL_SELECT_GAME_FOLDER, command=self.selectGameFolder)
        self.fileMenu.add_command(label=TopMenu.LABEL_SELECT_OUTPUT_FOLDER, command=self.selectOutputFolder)
        self.fileMenu.add_command(label=TopMenu.LABEL_WRITE_CHANGES, command=self.onWriteChanges)
        self.fileMenu.add_command(label=TopMenu.LABEL_EXIT, command=lambda: (self.onQuit(), root.quit()))

        self.menuBar.add_cascade(label="File", menu=self.fileMenu)
        self.disableWriteChangesItem()


    def selectGameFolder(self) -> None:
        self.onSelectConfigFolder(tkinter.filedialog.askdirectory())
    def selectOutputFolder(self) -> None:
        self.onSelectOutputFolder(tkinter.filedialog.askdirectory())

    def disableWriteChangesItem(self) -> None:
        self.disableMenuItem(TopMenu.LABEL_WRITE_CHANGES)

    def enableWriteChangesItem(self) -> None:
        self.enableMenuItem(TopMenu.LABEL_WRITE_CHANGES)

    def disableMenuItem(self, label) -> None:
        self.fileMenu.entryconfigure(label, state=tkinter.DISABLED)

    def enableMenuItem(self, label) -> None:
        self.fileMenu.entryconfigure(label, state=tkinter.NORMAL)


class MainController:
    def __init__(self) -> None:
        pass
    def onSelectElement(element: ETree.Element) -> None:
        
        pass

def isReadableFile(filePath) -> bool:
    return os.path.isfile(filePath) and os.access(filePath, os.R_OK)

def isReadableFolder(folderPath) -> bool:
    isDir = os.path.isdir(folderPath)
    accessOk = os.access(folderPath, os.R_OK)
    return isDir and accessOk 

def isWriteableFolder(folderPath) -> bool:
    return os.path.isdir(folderPath) and os.access(folderPath, os.W_OK)

def main():
    gui = XPathModifierGUI()
    gui.start()

if __name__ == "__main__":
    main()
