import requests
import csv
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import filedialog, Text
from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from PIL import Image, ImageTk
import threading
import sqlite3
import time
import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.dates import (
    DateFormatter, AutoDateLocator, AutoDateFormatter, datestr2num
)
from matplotlib import style
style.use('fivethirtyeight')

locationCsvFile = []

carsWithSameDecalsDup = []
carsWithSameDecals = []

currentLineArr=[]

def getCars():
    URL = "https://rl.insider.gg/en/pc"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:86.0) Gecko/20100101 Firefox/86.0"}
    page = requests.get(URL, headers=headers)
    suppe = BeautifulSoup(page.content, "html.parser")
    
    allCars = suppe.find_all("div",class_="itemNameSpan")
    
    for car in allCars:
        temp = car.text
        if "[" in temp:
            indexFirstBracket = temp.index("[")
            indexSecondBracket = temp.index("]")
            carsWithSameDecalsDup.append(temp[(indexFirstBracket+1):indexSecondBracket])
    
    for word in carsWithSameDecalsDup:
        if word not in carsWithSameDecals:
            carsWithSameDecals.append(word)

def checkLength():
    try:
        path = locationCsvFile[0]
    except:
        messagebox.showerror("Error Pepe :(","No or wrong file selected! Restart Programm!")
    file = open(path, newline= '')
    reader = csv.reader(file)

    header = next(reader)
    counter = 1
    for line in reader:
        slot = line[2]
        quality = line[7]
        crate = line[8]
        tradeable = line[9]
        if tradeable == "false":
            continue
        if slot == "Blueprint" or slot == "Player Title" or slot == "Player Anthem" or slot == "Engine Audio":
            continue
        if quality == "Premium" or quality == "UNKNOWN?":
            continue
        if crate == "?INT?TAGame.ProductSeries.Series544?":
            continue
        counter = counter + 1
    file.seek(0)
    next(reader)
    return counter

def isCarInName(itemname):
    for car in carsWithSameDecals:
        if car in itemname:
            return True
            break

def formatName(itemName):#ausnahmen: zomba, die decals für verschiedene bodies
    if ":" in itemName and isCarInName(itemName) == True:
        index = itemName.index(":")
        carName = itemName[:index]
        partName = itemName[(index+2):]
        return (partName+" ["+carName+"]")

    return itemName

def formatColor(itemColor):
    if itemColor == "none":
        itemColor = "Default"
        return itemColor
    elif itemColor == "Titanium White":
        itemColor = "White"
        return itemColor
    itemColor = itemColor.replace(" ","")
    return itemColor

def formatType(itemType):#art des items bsp tor explosion
    if itemType == "Player Banner":
        itemType = "banners"
        return itemType
    elif itemType == "Rocket Boost":
        itemType = "boosts"
        return itemType
    elif itemType == "Paint Finish":
        itemType = "paintFinishes"
        return itemType
    elif itemType == "Wheels":
        itemType = "wheels"
        return itemType
    elif itemType == "Body":
        itemType = "cars"
        return itemType
    elif itemType == "Animated Decal":
        itemType = "decals"
        return itemType
    elif itemType == "Goal Explosion":
        itemType = "goalExplosions"
        return itemType
    elif itemType == "Avatar Border":
        itemType = "avatarBorders"
        return itemType
    else:
        itemType = (itemType.lower()+"s")
        return itemType

def formatQuality(itemQuality):#aka rarity
    if itemQuality == "Very rare":
        itemQuality = "|veryRare|"
        return itemQuality
    elif itemQuality == "Black market":
        itemQuality = "|blackMarket|"
        return itemQuality
    else:
        itemQuality = "|"+itemQuality.lower()+"|"
        return itemQuality

def formatReturnedText(WrongPrice):
    if "&" in WrongPrice:
        indexFirst = WrongPrice.index("&")
        indexSecond = WrongPrice.rindex("p")
        
        if "k" in WrongPrice:
            priceHigh = float(WrongPrice[(indexSecond+1):(WrongPrice.index("k")-1)])
            priceHigh = priceHigh * 1000
            priceLow = float(WrongPrice[:indexFirst])
            priceLow = priceLow * 1000
        else:
            priceLow = float(WrongPrice[:indexFirst])
            priceHigh = float(WrongPrice[(indexSecond+1):])
        
        priceAvg = (priceLow + priceHigh)/2
    else:
        priceLow = 0
        priceHigh = 0
        priceAvg = 0

    priceLow = int(priceLow)
    priceHigh = int(priceHigh)
    priceAvg = int(priceAvg)

    return [priceLow,priceHigh,priceAvg]

def checkPrice(namen, color, typus, rarity):

    if rb.get() == 0:
        URL = "https://rl.insider.gg/en/pc"
    elif rb.get() == 1:
        URL = "https://rl.insider.gg/en/psn"
    elif rb.get() == 2:
        URL = "https://rl.insider.gg/en/xbox"
    elif rb.get() == 3:
        URL = "https://rl.insider.gg/en/switch"
    else:
        URL = "https://rl.insider.gg/en/pc"

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:86.0) Gecko/20100101 Firefox/86.0"}
    page = requests.get(URL, headers=headers)
    soup = BeautifulSoup(page.content, "html.parser")


    itemRow = soup.find(lambda tag: tag.name=="tr" and
			    tag.get("data-itemfullname")== namen and 
			    tag.get("data-itemtype") == typus and
                tag.get("data-itemrarity") ==rarity
                )

    
    if not itemRow:
        itemRow = soup.find("tr",{"data-itemfullname":namen})

    children = itemRow.find("td",class_="price" +color+ " priceRange")
    
    if children is None:
        temp = " "
    else:
        temp = children.text

    Preis = formatReturnedText(temp)
    return Preis

def mainMethod():
    path = locationCsvFile[0]
    file = open(path, newline= '')
    reader = csv.reader(file)
    writer = csv.writer(file)

    header = next(reader)
    
    getCars()

    totalWorthLow = 0
    totalWorthHigh = 0
    totalWorthAvg = 0
    totalWorthExcludeUnderVal = 0

    currentline = 1

    ownedCredits = 0

    try:
        if inputCreditsField.get() == '':
            ownedCredits = 0
        else:
            ownedCredits = int(inputCreditsField.get())
    except ValueError:
        messagebox.showerror("Error Pepe :(","Error: Input only numbers! Restart Programm!")
        return
    minValuelimit = 0

    try:
        if inputMinimumValue.get() == '':
            minValuelimit = 0
        else:
            minValuelimit = int(inputMinimumValue.get())
    except ValueError:
        messagebox.showerror("Error Pepe :(","Error: Input only numbers! Restart Programm!")
        return

    for row in reader:
        # row = [product id, name, slot, paint, certification, certification value, certification label, quality, crate, tradeable, amount, instanceid]
        name = row[1]
        slot = row[2]
        paint = row[3]
        quality = row[7]
        crate = row[8]
        tradeable = row[9]
        amount = row[10]
        if tradeable == "false":
            continue
        if slot == "Blueprint" or slot == "Player Title" or slot == "Player Anthem" or slot == "Engine Audio":
            continue
        if quality == "Premium" or quality == "UNKNOWN?":
            continue
        if crate == "?INT?TAGame.ProductSeries.Series544?":
            continue
        #es könnte noch verbessert werden, dass auch Blueprints berechnet werden
        #eventuell auch non crate aber eher weniger
        #items von anderen Plattformen werden mitberechnet
        #AUCH ANDERE PLATTFORMEN MÖGLICH DENN TRADEABLE IST TRUE

        

        
        currentline=currentline+1
        currentLineArr.append(currentline)
        progressText.config(text=(str(currentline)+"/"+str(checkLength())))
        stepProgressBarCalc()

        name = formatName(name)
        paint = formatColor(paint)
        slot = formatType(slot)
        quality = formatQuality(quality)

        try:
            PriceItem = checkPrice(name, paint, slot, quality)
        except:
            PriceItem = [0,0,0]

        if int(PriceItem[2])<minValuelimit:
            pass
        else:
            totalWorthExcludeUnderVal = totalWorthExcludeUnderVal + (int(PriceItem[2])*int(amount))

        totalWorthLow = totalWorthLow + (int(PriceItem[0])*int(amount))
        totalWorthHigh = totalWorthHigh + (int(PriceItem[1])*int(amount))
        totalWorthAvg = totalWorthAvg + (int(PriceItem[2])*int(amount))

    try:
        totalWorthLow = totalWorthLow + ownedCredits
    except:
        totalWorthLow = "0"

    try:
        totalWorthHigh = totalWorthHigh + ownedCredits
    except:
        totalWorthHigh = "0"

    try:
        totalWorthAvg = totalWorthAvg + ownedCredits
    except:
        totalWorthAvg = "0"

    try:
        totalWorthExcludeUnderVal = totalWorthExcludeUnderVal + ownedCredits
    except:
        totalWorthExcludeUnderVal = "0"
        
    return [totalWorthLow,totalWorthHigh,totalWorthAvg,totalWorthExcludeUnderVal]

root = tk.Tk()
root.title('Inventory Pepe')
root.wm_iconbitmap('.\sources\icon.ico')
root.iconbitmap('.\sources\icon.ico')

frameDBScreen = LabelFrame(root)
frameDBScreen.grid(column=0,row=0)

frameCalculationScreen = LabelFrame(root)
frameCalculationScreen.grid(column=0,row=0)

frameResult = LabelFrame(root)
frameResult.grid(column=0,row=0,sticky=NSEW)

frameMainMenu = LabelFrame(root)
frameMainMenu.grid(column=0,row=0,sticky=NSEW)

#frameCalculation Screen============================================================================

#logo
my_logo = ImageTk.PhotoImage(Image.open(".\sources\logo_pepe_600.png"))
my_label = Label(frameCalculationScreen,image=my_logo)
my_label.grid(columnspan=2,column=1,row=0,pady=50,padx=6)

#radiobutton
rb = IntVar()

pcImage = PhotoImage(file='.\sources\pc_64.png')
psnImage = PhotoImage(file='.\sources\psn_64.png')
xboxImage = PhotoImage(file='.\sources\Xbox_64.png')
switchImage = PhotoImage(file='.\sources\switch_64.png')

radiobuttonPc = Radiobutton(frameCalculationScreen, text="PC",variable=rb,value=0,image=pcImage,indicatoron=0,relief=FLAT)
radiobuttonPc.grid(columnspan=1,column=0,row=1,pady=30,padx=50)

radiobuttonPsn = Radiobutton(frameCalculationScreen, text="PSN",variable=rb,value=1,image=psnImage,indicatoron=0,relief=FLAT)
radiobuttonPsn.grid(columnspan=1,column=1,row=1,pady=30,padx=30)

radiobuttonXbox = Radiobutton(frameCalculationScreen, text="Xbox",variable=rb,value=2,image=xboxImage,indicatoron=0,relief=FLAT)
radiobuttonXbox.grid(columnspan=1,column=2,row=1,pady=30,padx=30)

radiobuttonSwitch = Radiobutton(frameCalculationScreen, text="Switch",variable=rb,value=3,image=switchImage,indicatoron=0,relief=FLAT)
radiobuttonSwitch.grid(columnspan=1,column=3,row=1,pady=30,padx=30)

#text choose file
chooseFileText = tk.Label(frameCalculationScreen, text="Choose file:",font="Verdana")
chooseFileText.grid(columnspan=2,column=0,row=2,sticky=E,pady=10)

def openFile():
    browse_text.set("loading...")
    fileLoc = filedialog.askopenfilename(initialdir="/",parent=frameCalculationScreen,title="Choose the CSV-File",filetype=[("CSV file","*.csv")])
    if fileLoc:
        browse_text.set("Success!")
        locationCsvFile.append(fileLoc)

#browse text button
browse_text = tk.StringVar()
brose_btn = tk.Button(frameCalculationScreen, textvariable=browse_text,command=lambda:openFile(), font="Verdana",bg="white",fg="#498201",width=10)
browse_text.set("Browse")
brose_btn.grid(column=2, row=2,pady=10)

#text minimum value
minimumValueText = tk.Label(frameCalculationScreen,text="Only include items over:",font="Verdana")
minimumValueText.grid(columnspan=2,column=0,row=4,sticky=E,pady=10)

#entry minimum value
inputMinimumValue = Entry(frameCalculationScreen,width=22)
inputMinimumValue.grid(columnspan=1, column=2,row=4,pady=10)

#Text give credits
creditsText = tk.Label(frameCalculationScreen,text="How many credits do you have:",font="Verdana")
creditsText.grid(columnspan=2,column=0,row=3,sticky=E,pady=10)

#input credits
inputCreditsField = Entry(frameCalculationScreen,width=22)
inputCreditsField.grid(columnspan=1,column=2,row=3,pady=10)
#userCredits = inputCreditsField.get()


#start methode
def startCalculating():
    inputCreditsField.config(state='disabled')
    inputMinimumValue.config(state='disabled')
    numberOfLines = checkLength()
    damn = mainMethod()

    textExcValue = tk.Label(frameResult,text="",font="Verdana")
    textExcValue.grid(columnspan=1,column=2,row=2,padx=30)

    valueExcValue = tk.Label(frameResult,text="",font="Verdana")
    valueExcValue.grid(columnspan=1,column=3,row=2,padx=30)

    global minvaluefinal
    minvaluefinal = int(damn[0])
    global maxvaluefinal
    maxvaluefinal = int(damn[1])
    global avgvaluefinal
    avgvaluefinal = int(damn[2])

    valueMinValue.config(text=minvaluefinal)
    valueMaxValue.config(text=maxvaluefinal)
    valueAvgValue.config(text=avgvaluefinal)

    try:
        if int(inputMinimumValue.get()) > 0:
            textExcValue.config(text=("Items over "+str(inputMinimumValue.get())+" credits (avg):"))

            valueExcValue.config(text=(damn[3]))
    except:
        pass

    frameResult.tkraise()
    
   

#start button
start_btn = tk.Button(frameCalculationScreen, text="Calculate",command=threading.Thread(target=startCalculating).start,font="Verdana",bg="#498201",fg="white")
start_btn.grid(columnspan=1,column=3,row=6,pady=30,padx=60,sticky=W)

#methode progressbar
def stepProgressBarCalc():
    progressBarCalc['value'] = (currentLineArr[-1]/checkLength())*100
    root.update_idletasks()

#progress bar
progressBarCalc = ttk.Progressbar(frameCalculationScreen, orient=HORIZONTAL,length=600,mode="determinate")
progressBarCalc.grid(columnspan=2,column=1,row=6,sticky=E)

#progresstext
progressText = tk.Label(frameCalculationScreen,text=("0/0"),font="Verdana")
progressText.grid(columnspan=1,column=0,row=6,sticky=W,padx=30)

def backToMain():
    frameMainMenu.tkraise()

backFromCalculationBtn = tk.Button(frameCalculationScreen,text="Back",command=backToMain,font="Verdana")
backFromCalculationBtn.grid(column=0,row=0,sticky=NW,pady=30,padx=50)

#frameMainMenu====================================================================================

my_label = Label(frameMainMenu,image=my_logo)
my_label.grid(columnspan=3,column=0,row=0,pady=50)

def showWindowCalculation():
    frameCalculationScreen.tkraise()

calculateInventoryBtn = tk.Button(frameMainMenu,text="Calculate inventory",command=showWindowCalculation,font="Verdana",bg="#498201",fg="white",width = 50)
calculateInventoryBtn.grid(columnspan=1,column=1,row=1,pady=80,padx=150)

def graphData():
    conn = sqlite3.connect('.\sources\inventory_performance.db')
    cursor = conn.cursor()

    cursor.execute("SELECT date,avgvalue,minvalue,maxvalue FROM dataset")
    dates = []
    avgPrices = []
    minPrices = []
    maxPrices = []

    for row in cursor.fetchall():
        dates.append(datestr2num(row[0]))
        avgPrices.append(row[1])
        minPrices.append(row[2])
        maxPrices.append(row[3])


    conn.commit()
    conn.close()

    plt.plot_date(dates,avgPrices,'-',label='Avg value')
    plt.plot_date(dates,minPrices,'-',label='Min value')
    plt.plot_date(dates,maxPrices,'-',label='Max Value')
    plt.xlabel('Date')
    plt.ylabel('Value in Credits')
    plt.title('Inventory Performance')
    plt.legend()
    plt.show()

showHistoryBtn = tk.Button(frameMainMenu,text="Inventory Performance",command=graphData,font="Verdana",bg="#498201",fg="white",width = 50)
showHistoryBtn.grid(columnspan=1,column=1,row=2)

#frame result screen================================================================================

my_label = Label(frameResult,image=my_logo)
my_label.grid(columnspan=4,column=0,row=0,pady=50,padx=178)

textMinValue = tk.Label(frameResult,text="Minimum value:",font="Verdana")
textMinValue.grid(columnspan=1,column=0,row=1,padx=30)

textMaxValue = tk.Label(frameResult,text="Maximum value:",font="Verdana")
textMaxValue.grid(columnspan=1,column=0,row=2,padx=30)

textAvgValue = tk.Label(frameResult,text="Average value:",font="Verdana")
textAvgValue.grid(columnspan=1,column=2,row=1,padx=30)

valueMinValue = tk.Label(frameResult,text="",font="Verdana")
valueMinValue.grid(columnspan=1,column=1,row=1,padx=30)

valueMaxValue = tk.Label(frameResult,text="",font="Verdana")
valueMaxValue.grid(columnspan=1,column=1,row=2,padx=30)

valueAvgValue = tk.Label(frameResult,text="",font="Verdana")
valueAvgValue.grid(columnspan=1,column=3,row=1,padx=30)

backFromCalculationBtn = tk.Button(frameResult,text="Back",command=backToMain,font="Verdana")
backFromCalculationBtn.grid(column=0,row=0,sticky=NW,pady=30,padx=50)

conn = sqlite3.connect('.\sources\inventory_performance.db')

cursor = conn.cursor()

#create db
#cursor.execute("CREATE TABLE dataset (date TEXT,minvalue INTEGER,maxvalue INTEGER,avgvalue INTEGER)")

def submit():
    conn = sqlite3.connect('.\sources\inventory_performance.db')
    cursor = conn.cursor()

    time = datetime.datetime.now()
    cursor.execute("INSERT INTO dataset VALUES (?,?,?,?)",
    (time,minvaluefinal,maxvaluefinal,avgvaluefinal))

    conn.commit()
    conn.close()

saveResultButton = tk.Button(frameResult,text="Save result",command=submit,font="Verdana",bg="#498201",fg="white")
saveResultButton.grid(columnspan=1,column=1,row=3,pady=100)

showPerformanceButton = tk.Button(frameResult,text="Show Inventory Performance",command=graphData,font="Verdana",bg="#498201",fg="white")
showPerformanceButton.grid(columnspan=1,column=2,row=3)
conn.close()

root.mainloop()