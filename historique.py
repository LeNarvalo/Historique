#-*- coding:utf-8 -*-
import sqlite3, time, psutil, os, tooltip, threading,win32process
from urllib.request import urlopen
from tkinter import *
from tkinter import messagebox
from tkinter.font import Font
from functools import partial

master=Tk()
master.configure(background='#fafafb')
master.title("Historique")
chemin = os.path.expanduser('~\Historique')
chemin_historique = os.path.expanduser('~\AppData\Roaming\Mozilla\Firefox\Profiles\\')   #7tmziicy.default-release/places.sqlite
for o in os.listdir(chemin_historique):
	if "default-release" in o:
		if chemin_historique.endswith('Profiles\\'):
			chemin_historique+= o+'\\places.sqlite'
		else:
			messagebox.showinfo("Non compatible", '''Il semblerait que vous ayez plusieurs profils existants sur Firefox !\nPour le moment le logiciel ne prend pas en compte ce cas de figure... Désolé !''')
			master.exit()
#print(chemin_historique)


if not os.path.exists(chemin):  
	os.mkdir(chemin)

def write():
	file = open(chemin+"\\Params.txt","w")
	for website in websites:
		file.write("<•••>"+website[0]+"<•••>"+str(website[1])+"<•••>"+website[2]+"<•••>\n")
	file.close()

try:
	file = open(chemin+"\\Params.txt","r")
	a = file.readlines()
	websites = [[d,int(e),f] for d,e,f in [[c[1],c[2],c[3]] for c in [b.split("<•••>") for b in a]]]
	file.close()
except:
	websites = [['Youtube',0,'www.youtube.com'], ['Facebook',0,'www.facebook.com'],['Google Search',0,'www.google.com'],['Instagram',0,'www.instagram.com']]
	write()

def change_params(event):
	website = event.widget.cget("text")
	for w in websites:
		if website == w[0]:
			w[1]=1-w[1]
			#print('NEW :',w[0],w[1])
			break
	write()

def deleteRecord(sqliteConnection, cursor, idList): #[(4,),(3,)]
	try:
		#print("Connected to SQLite")
		# Get origin_id records
		origin_ids = []
		for id in idList:
			try:
				cursor.execute("""SELECT * FROM moz_places WHERE id = """+str(id[0]))
				line = cursor.fetchone()
				origin_ids.append((line[-1],))
			except:
				None

		# Get anno_attribute_id records
		anno_attribute_ids = []
		for id in idList:
			try:
				cursor.execute("""SELECT * FROM moz_annos WHERE place_id = """+str(id[0]))
				line = cursor.fetchone()
				anno_attribute_ids.append((line[2],))
			except:
				None

		# Deleting multiple records
		sql_delete_query = """DELETE FROM moz_places WHERE id = ?"""
		cursor.executemany(sql_delete_query,idList)
		sqliteConnection.commit()
		
		# Deleting related records
		# 1. Deleting place_id related records
		mozs=["moz_inputhistory","moz_historyvisits","moz_annos"]
		for moz in mozs:
			sql_delete_query = ("DELETE FROM "+moz+" WHERE place_id = ?")
			cursor.executemany(sql_delete_query, idList)
			sqliteConnection.commit()

		# 2. Deleting anno_attributes_id related records
		sql_delete_query = ("DELETE FROM moz_anno_attributes WHERE id = ?")
		cursor.executemany(sql_delete_query, anno_attribute_ids)
		sqliteConnection.commit()

		# 3. Deleting origin_id related records
		sql_delete_query = ("DELETE FROM moz_origins WHERE id = ?")
		cursor.executemany(sql_delete_query, origin_ids)
		sqliteConnection.commit()

		#print("Record deleted successfully")
		cursor.close()

	except sqlite3.Error as error:
		print("Failed to delete record from sqlite table", error)
	finally:
		if (sqliteConnection):
			sqliteConnection.close()
			#print("the sqlite connection is closed")
			master.withdraw()

def delete():
	websites_to_del = []
	for w in websites:
		if w[1]:
			websites_to_del.append(w[2])

	#CORRECTIF A FAIRE SUR LE CHEMIN
	sqliteConnection = sqlite3.connect(chemin_historique)
	cursor = sqliteConnection.cursor()
	cursor.execute("""SELECT * FROM moz_places""")

	ids = []
	mod_ids = []
	for l in cursor:
		try:
			seconds = l[8]/1000000
			if seconds > starting:
				for w in websites_to_del:
					if w in l[1]:
						ids.append((l[0],))
						#print(l[0],l[2], "TO DEL")
		except:
			mod_ids.append(l[0])

	t = str(time.time()).replace(".","")
	t += "000000"
	t = t[:16]
	
	for id in mod_ids:
		#print(id,' updated')
		cursor.execute("UPDATE moz_places SET last_visit_date = "+t+" WHERE id = "+str(id))
		sqliteConnection.commit()
		#cursor.close()
		#sqliteConnection.close()
	
	print("L'historique depuis le dernier démarrage de Firefox contient "+str(len(ids))+" éléments à supprimer.")
	
	if len(ids):
		deleteRecord(sqliteConnection, cursor, ids)
	else:
		master.withdraw()
		

def display_websites():
	global  vars, frame
	try:
		for widget in frame.winfo_children():
			widget.destroy()
		frame.pack_forget()
	except:
		None
	frame = Frame(master, bg='#fafafb')
	frame.grid(row=1,column=0,columnspan=3)
	c = 0
	r = 0
	vars = []
	for website in websites:
		#print(website)
		var = IntVar(value=website[1])
		vars.append(var)
		if len(website[0])>15:
			name = website[0][:15]+"..."
		else:
			name = website[0]
		bouton=Checkbutton(frame, text=name, takefocus=False, variable=var,bg='#fafafb',activebackground='#fafafb',fg="black",activeforeground="#6a737c",selectcolor="white",anchor=W)
		tooltip.register(bouton, website[2])
		bouton.grid(row=r,column=c,sticky=W, padx=15)
		bouton.bind("<ButtonRelease-1>", change_params)
		bouton.bind("<ButtonRelease-3>", remove_website)
		if c < 2:
			c+=1
		else:
			c=0
			r+=1
	write()

def windowExit(event):
	global window, nwName, nwURL, r
	try:
		if event.keysym == 'Return':
			event=1
		elif event.keysym == 'Escape':
			event=0
	except:
		None
	if event:
		if len(nwName.get())<2:
			messagebox.showinfo("Trop court", '''Merci de rentrer un nom d'au moins 2 caractères !\n''')
			return
		for w in websites:
			if nwName.get() == w[0]:
				messagebox.showinfo("Déjà existant", '''Ce site est déjà dans la liste !\n''')
				return
		try:
			for w in websites:
				if nwURL.get() == w[2]:
					messagebox.showinfo("Déjà existant", '''Ce site est déjà dans la liste !\n''')
					return
			urlopen('http://'+nwURL.get())
			file = open(chemin+"\\Params.txt","a")
			file.write("<•••>"+nwName.get()+"<•••>1<•••>"+nwURL.get()+"<•••>\n")
			file.close()
			websites.append([nwName.get().capitalize(),1,nwURL.get().lower()])
			nwName.set("")
			nwURL.set("")
			display_websites()
			entreeName.focus_set()
		except:
			messagebox.showinfo("Site inconnu", '''Merci de saisir une URL correcte, ex : www.google.com !\n''')
			return

	else:
		window.destroy()

def capitalize(event):
	try:
		nwName.set(nwName.get()[0].upper()+nwName.get()[1:])
	except:
		None

def minimize(event):
	nwURL.set(nwURL.get().lower())

def add():
	global nwName, nwURL, window, entreeName
	window = Toplevel(master)
	master.eval(f'tk::PlaceWindow {str(window)} center')
	labelName = Label(window, text="Nom du site (Ex: Youtube) :")	
	labelName.grid(row=0,column = 0,sticky=W)	
	nwName=StringVar()
	entreeName= Entry(window, textvariable=nwName, width=30)	
	entreeName.grid(row=0,column = 1, sticky=W)
	entreeName.focus_set()
	entreeName.bind('<Key>', capitalize)
	labelURL = Label(window, text="URL (Ex: www.youtube.com) :")	
	labelURL.grid(row=1,column = 0,sticky=W)
	nwURL=StringVar()
	entreeURL= Entry(window, textvariable=nwURL, width=30)	
	entreeURL.grid(row=1,column = 1, sticky=W)
	entreeURL.bind('<Key>', minimize)
	frame = Frame(window)
	frame.grid(row=2,column=0,columnspan=2,sticky=NSEW)
	ADD = Button(frame, overrelief=GROOVE, text ='+', command=partial(windowExit,1))
	ADD.pack(side=LEFT,fill=X,expand=1)
	window.bind('<Return>', windowExit)
	window.bind('<Escape>', windowExit)
	ESC = Button(frame, overrelief=GROOVE, text ='Quitter', command=partial(windowExit,0))
	ESC.pack(side=LEFT,fill=X,expand=1)
	window.transient(master)

def remove_website(event):
	global websites
	website = event.widget.cget("text")
	windowsAnswer = messagebox.askyesno("Supprimer?", "Vous-les vous supprimer "+website+" de la liste ?")
	if windowsAnswer:
		tempory_Websites = []
		for w in websites:
			if website != w[0]:
				tempory_Websites.append(w)
		#print(tempory_Websites)
		websites = tempory_Websites.copy()
		#print(websites)
		display_websites()

def testFirefox():
	global starting
	start_time=9999999999
	pids = []
	firefox_pids = []
	over = True
	while 1:
		try:
			current_pids = list(win32process.EnumProcesses())
			if start_time ==9999999999:
				diff = list(set(current_pids)-set(pids))
				pids=current_pids.copy()
				for pid in diff:
					try:
						#print(psutil.Process(pid).name())
						if "firefox" in psutil.Process(pid).name():
							#print("FIREFOX FOUND")
							firefox_pids.append(pid)
							over = False
							p_time = psutil.Process(pid).create_time()
							if start_time > p_time:
								start_time = p_time
								print("Firefox start to :",time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time)))
					except:
						None
			elif pids != current_pids:
				diff_re =  list(set(pids)-set(current_pids)) #liste de pids terminés
				diff_ad =  list(set(current_pids)-set(pids)) #liste de pids ajoutés
				#print('PIDS DIFFERENT removed :',diff_re,' added :',diff_ad)
				pids=current_pids.copy()
				#print("FIREFOX_PIDS before remove : ",firefox_pids)
				for pid in diff_re:
					if pid in firefox_pids:
						firefox_pids.remove(pid)
				#print("FIREFOX_PIDS after remove : ",firefox_pids)
				for pid in diff_ad:
					try:
						if "firefox" in psutil.Process(pid).name():
							firefox_pids.append(pid)
					except:
						None
				#print("FIREFOX_PIDS after add : ",firefox_pids)
		except:
			#print("BUUUGG")
			None

		if not firefox_pids and start_time != 9999999999 and not over:
			print('FIREFOX IS OVER')
			over=True
			starting=start_time
			start_time = 9999999999
			master.deiconify()
			master.attributes("-topmost", True)
		time.sleep(0.5)

def disable_event():
	master.withdraw()

def fenetre():
	x = (master.winfo_screenwidth()*0.85 - master.winfo_reqwidth())/2
	y = (master.winfo_screenheight()*0.70 - master.winfo_reqheight())/2
	master.geometry("+%d+%d" % (x, y))
	master.resizable(False, False)

	r = 0
	Label(master, text="Voulez-vous supprimer l'historique ?",bg='#fafafb',fg="black",font=Font(family='Helvetica',  size=11, weight='bold'), ).grid(row=r,column=0, columnspan=3, sticky=W)

	display_websites()

	r = 2
	Delete = Button(master,width=20, text ='Supprimer l\'historique', bg='#e64235', activebackground='#e64235', fg="white", command=delete)
	Delete.grid(row=r,column=0,pady=5)
	Add = Button(master,width=20, text ='Ajouter un site', bg='#35d1e6', activebackground='#35d1e6', fg="white", command=add)
	Add.grid(row=r,column=2,pady=5)

fenetre()
master.withdraw()
#master.deiconify()
threading.Timer(1,testFirefox).start() 	
master.protocol("WM_DELETE_WINDOW", disable_event)
master.mainloop()
