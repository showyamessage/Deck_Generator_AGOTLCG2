import time
import streamlit as st
#import plotly.express as px
import pandas as pd

# =============================================================================
# Funktionen
# =============================================================================
def GetCardsInDecks(dfCards,dfDecks):
    # Number of one Card with Number of copies in deck
    #!!!!!decks created since release HERE!!!!
    dictCodeName = allcards[['code', 'name']].set_index('code').to_dict()['name']
    dfCards1 = dfCards.copy()
    dfCards1['releaseDates_byname'] = dfCards1.apply (lambda rowCards: [i for i in dfCards1[dfCards1["name"] == rowCards["name"]]["available"].tolist()], axis=1)
    dfCards1['minDateVersion'] = dfCards1.apply (lambda rowCards: min(rowCards['releaseDates_byname']), axis=1)
    
    #decks created since release
    dfCards1['decksCREATEDsincerelease'] = dfCards1.apply (lambda rowCards: len(dfDecks[dfDecks["date_creation"] >= rowCards["available"]]), axis=1)    
    dfCards1 = dfCards1[dfCards1['decksCREATEDsincerelease'] != 0]
    dfCards1['decksCREATEDsincerelease_byname'] = dfCards1.apply (lambda rowCards: rowCards['decksCREATEDsincerelease'] if len(rowCards['releaseDates_byname']) == 1 else len(dfDecks[dfDecks["date_creation"] >= rowCards['minDateVersion']]), axis=1)
    my_bar.progress(1)
    
    #deckcount
    dfCards1['deckcount'] = dfCards1.apply(lambda rowCards: len(dfDecks[dfDecks.apply(lambda rowDecks: rowCards['code'] in rowDecks["slots"].keys(), axis=1)]), axis=1)
    dfCards1 = dfCards1[dfCards1['deckcount'] > 0]
    
    dfCards2 = dfCards1.copy()
    dfCards2['deckcount'] = dfCards2.apply(lambda rowCards: len(dfDecks[dfDecks.apply(lambda rowDecks: rowCards['code'] in rowDecks["slots"].keys() and rowDecks["slots"][rowCards['code']] >= 2, axis=1)]), axis=1)
    dfCards2 = dfCards2[dfCards2['deckcount'] > 0]
    my_bar.progress(27)
    
    dfCards3 = dfCards2.copy()
    dfCards3['deckcount'] = dfCards3.apply(lambda rowCards: len(dfDecks[dfDecks.apply(lambda rowDecks: rowCards['code'] in rowDecks["slots"].keys() and rowDecks["slots"][rowCards['code']] >= 3, axis=1)]), axis=1)
    dfCards3 = dfCards3[dfCards3['deckcount'] > 0]
    
    
    dfCards1['copy'] = 1
    dfCards2['copy'] = 2
    dfCards3['copy'] = 3
    dfTripleCards = pd.concat([dfCards1, dfCards2, dfCards3]).reset_index()
    dfTripleCards['identifier'] = dfTripleCards.apply(lambda row: row['label'] + "#" + str(row['copy']), axis=1)
    my_bar.progress(40)
    
    #deckcount by Name
    dfTripleCards['deckcount_byname'] = dfTripleCards.apply(lambda rowCards: rowCards['deckcount'] if len(rowCards['releaseDates_byname']) == 1 else len(dfDecks[dfDecks.apply(lambda rowDecks: (rowCards['name'] in [dictCodeName[code] for code in rowDecks["slots"].keys() if rowDecks["slots"][code]>= rowCards["copy"]]) if rowDecks["date_creation"] >= rowCards['minDateVersion'] else False, axis=1)]), axis=1)
    my_bar.progress(99)
    
    #Calculation
    dfTripleCards['in decks'] = dfTripleCards.apply (lambda rowCards: rowCards['deckcount']/rowCards['decksCREATEDsincerelease'], axis=1)
    dfTripleCards['in decks_byname'] = dfTripleCards.apply (lambda rowCards: rowCards['deckcount_byname']/rowCards['decksCREATEDsincerelease_byname'], axis=1)
    dfTripleCards['max(in decks, in decks_byname)'] = dfTripleCards.apply (lambda rowCards: max(rowCards['in decks'],rowCards['in decks_byname']), axis=1)
    dfTripleCards = dfTripleCards.sort_values(['max(in decks, in decks_byname)', 'in decks', 'in decks_byname'], ascending = False, axis = 0) 
    return dfTripleCards

def GenerateDecklist(dfFinal, RL, totalcards, totalplots, includeCharacters, includeLimiteds, DoNotUsePacks):
    includelocationsattachmentsevents = totalcards-includeCharacters
    
    dfFinal['final'] =""
    dfFinal.loc[dfFinal.apply (lambda rowCards: rowCards["code"] in RL['banned'], axis=1),'final'] = "banned"
    dfFinal.loc[(dfFinal.pack_name.isin(DoNotUsePacks)),'final'] = "donotusepack"
    dfFinal.loc[(dfFinal.type_code == 'agenda'),'final'] = "agenda"
    

            
    #Select Cards
    blChosenRestricted = False
    dctPodsChosen = {i['title']: False for i in RL['restricted_pods']}
    countPlots = 0
    countCards = 0
    countLimiteds = 0
    countCharacters = 0
    countlocationsattachmentsevents = 0
    dfFinal = dfFinal.sort_values(['max(in decks, in decks_byname)', 'in decks', 'in decks_byname'], ascending = False, axis = 0)
    dfFinal = dfFinal.reset_index()
    for index, row in dfFinal.iterrows():
        if countCards < totalcards or countPlots < totalplots:
            if row['final'] == "":
                blIsRestricted = row['code'] in RL['restricted']
                blChosenPod = False
                TitlePods = []
                for i in dctPodsChosen.keys():
                    if row['code'] in [x for x in RL['restricted_pods'] if x['title'] == i][0]['cards']:
                        TitlePods.append(i)
                for i in TitlePods:
                    if dctPodsChosen[i]:
                        blChosenPod = True
                if not blIsRestricted or (not blChosenRestricted) or (blChosenRestricted and 0 < len(dfFinal[dfFinal.apply (lambda rowCards: rowCards['final']==1 and rowCards['code'] == row['code'], axis=1)])):
                    if not blChosenPod or (blChosenPod and 0 < len(dfFinal[dfFinal.apply (lambda rowCards: rowCards['final']==1 and rowCards['code'] == row['code'], axis=1)])):
                    
                        if 0 < len(dfFinal[dfFinal.apply (lambda rowCards: rowCards['final']==1 and rowCards['name'] == row['name'] and (rowCards['label'] != row['label']), axis=1)]):
                            dfFinal.at[index, 'final'] = "otherversions" #row['final'] = "otherversions"
                        else:
                            if row["text"].find("Limited.") == -1: #NO LIMITED
                                if row["type_code"] == "character": #CHARACTER
                                    if countCharacters < includeCharacters: #CHARACTER LEFT
                                        dfFinal.at[index, 'final'] = 1 #row['final'] = 1
                                        countCharacters += 1
                                        countCards += 1
                                        if blIsRestricted:
                                            blChosenRestricted = True
                                        for i in TitlePods:
                                            dctPodsChosen[i]= True
                                    else: #CHARACTER FULL
                                        dfFinal.at[index, 'final'] = "othercharacters" #row['final'] = "othercharacters"
                                elif row["type_code"] == "plot":
                                    if countPlots < totalplots: #PLOTS LEFT
                                        dfFinal.at[index, 'final'] = 1 #row['final'] = 1
                                        countPlots += 1
                                        if blIsRestricted:
                                            blChosenRestricted = True
                                        for i in TitlePods:
                                            dctPodsChosen[i]= True                   
                                    else: #PLOTS FULL
                                        dfFinal.at[index, 'final'] = "otherplots" #row['final'] = "otherplots"
                                else: #NO CHARACTER NO PLOT
                                    if countlocationsattachmentsevents < includelocationsattachmentsevents: #NON-CHARACTER LEFT
                                        dfFinal.at[index, 'final'] = 1 #row['final'] = 1
                                        countlocationsattachmentsevents += 1
                                        countCards += 1
                                        if blIsRestricted:
                                            blChosenRestricted = True
                                        for i in TitlePods:
                                            dctPodsChosen[i]= True
                                    else: #NON-CHARACTER FULL
                                        dfFinal.at[index, 'final'] = "otherlocationsattachmentsevents" #row['final'] = "otherlocationsattachmentsevents"
                            else: #limited
                                if countLimiteds < includeLimiteds:
                                    if row["type_code"] == "character": #CHARACTER
                                        if countCharacters < includeCharacters: #CHARACTER LEFT
                                            dfFinal.at[index, 'final'] = 1 #row['final'] = 1
                                            countCharacters += 1
                                            countCards += 1
                                            countLimiteds += 1
                                            if blIsRestricted:
                                                blChosenRestricted = True
                                            for i in TitlePods:
                                                dctPodsChosen[i]= True
                                        else: #CHARACTER FULL
                                            dfFinal.at[index, 'final'] = "othercharacters" #row['final'] = "othercharacters"
                                    else: #NO CHARACTER
                                        if countlocationsattachmentsevents < includelocationsattachmentsevents: #NON-CHARACTER LEFT
                                            dfFinal.at[index, 'final'] = 1 #row['final'] = 1
                                            countlocationsattachmentsevents += 1
                                            countCards += 1
                                            countLimiteds += 1
                                            if blIsRestricted:
                                                blChosenRestricted = True
                                            for i in TitlePods:
                                                dctPodsChosen[i]= True
                                        else: #NON-CHARACTER FULL
                                            dfFinal.at[index, 'final'] = "otherlocationsattachmentsevents" #row['final'] = "otherlocationsattachmentsevents"
                                else:
                                    dfFinal.at[index, 'final'] = "otherlimiteds" #row['final'] = "otherlimiteds"
                    else:
                        dfFinal.at[index, 'final'] = "otherpods" #row['final'] = "otherpods"
                else:
                    dfFinal.at[index, 'final'] = "otherrestricted" #row['final'] = "otherrestricted"
            elif row['final'] == "banned":
                dfFinal.at[index, 'final'] = "banned1"
            elif row['final'] == "donotusepack":
                dfFinal.at[index, 'final'] = "donotusepack1"
    return dfFinal

def get_Decklist(dfDeck):
    dfDeck = dfDeck[dfDeck['final'] == 1].sort_values('label', ascending = True, axis = 0)
    #by type
    dfPlots = dfDeck[dfDeck['type_code'] == "plot"].groupby(['label'], sort=False)['copy'].max()
    dfCharacters = dfDeck[dfDeck['type_code'] == "character"].groupby(['label'], sort=False)['copy'].max()
    dfAttachments = dfDeck[dfDeck['type_code'] == "attachment"].groupby(['label'], sort=False)['copy'].max()
    dfLocations = dfDeck[dfDeck['type_code'] == "location"].groupby(['label'], sort=False)['copy'].max()
    dfEvents = dfDeck[dfDeck['type_code'] == "event"].groupby(['label'], sort=False)['copy'].max()
    
    #dict
    dictPlots = dfPlots.to_dict()
    dictCharacters = dfCharacters.to_dict()
    dictAttachments = dfAttachments.to_dict()
    dictLocations = dfLocations.to_dict()
    dictEvents = dfEvents.to_dict()
    
    #str
    strPlots = "**Plots:**" + "  \n"  + "  \n".join([str(dictPlots[i]) + "x " + i for i in dictPlots])
    strCharacters = "**Characters:**" + "  \n"  + "  \n".join([str(dictCharacters[i]) + "x " + i for i in dictCharacters])
    strAttachments = "**Attachments:**" + "  \n"  + "  \n".join([str(dictAttachments[i]) + "x " + i for i in dictAttachments])
    strLocations = "**Locations:**" + "  \n"  + "  \n".join([str(dictLocations[i]) + "x " + i for i in dictLocations])
    strEvents = "**Events:**" + "  \n"  + "  \n".join([str(dictEvents[i]) + "x " + i for i in dictEvents])
    
    Decklist = strPlots + "\n" + "\n" +  strCharacters + "\n" + "\n" +  strLocations + "\n" + "\n" + strAttachments + "\n" + "\n" + strEvents
    return Decklist

def get_Notes(dfNotes):
    #How many Cards by Type should be in the notes?
    noteagendas = 6
    noteplots = 15
    notedrawdeck = 60
    # notecharacters = 30
    # notelocations = 20
    # noteattachments = 15
    # noteevents = 15
    
    #Don't Show banned cards + sort
    dfNotes = dfNotes[dfNotes['final'] != "banned"].sort_values(['in decks', 'index'], ascending = False, axis = 0)
    dfNotes = dfNotes[dfNotes['final'] != "donotusepack"].sort_values(['in decks', 'index'], ascending = False, axis = 0)
    #Cards not in Deck
    dfDonotusepack = dfNotes[dfNotes['final'] == "donotusepack1"]
    dfBanned = dfNotes[dfNotes['final'] == "banned1"]
    dfAgendas = dfNotes[dfNotes['final'] == "agenda"] #Would have made it. But Agendas don't get chosen
    dfOtherVersions = dfNotes[dfNotes['final'] == "otherversions"] #Would have made it. But Other Versions are more used
    dfOtherRestricted = dfNotes[dfNotes['final'] == "otherrestricted"] #Would have made it. But other restricted Card is more used
    dfPods = dfNotes[dfNotes['final'] == "otherpods"] #Would have made it. But other Card in the Pod is more used
    dfLimiteds = dfNotes[dfNotes['final'] == "otherlimiteds"] #Would have made it. But exclusion because of a maximum of limited cards and other limited Cards are more used
    #Other Cards
    dfTypes = dfNotes[~dfNotes.final.isin([1, "agenda", "otherversions", "otherrestricted", "otherpods", "otherlimiteds", "banned1", "donotusepack1"])]
    dfPlots = dfTypes[dfTypes['type_code'] == "plot"]
    dfDrawdeck = dfTypes[dfTypes['type_code'] != "plot"]
    # dfCharacters = dfTypes[dfTypes['type_code'] == "character"]
    # dfAttachments = dfTypes[dfTypes['type_code'] == "attachment"]
    # dfLocations = dfTypes[dfTypes['type_code'] == "location"]
    # dfEvents = dfTypes[dfTypes['type_code'] == "event"]
    # #LIMITEDS vs Non-limiteds?    
    
    #INCLUDED BY NAME Documentation
    dfDeck =  dfNotes[(dfNotes['final'] == 1) & (dfNotes['type_code'] == 'character')]#!= "plot")]
    dfDeckPlots =  dfNotes[(dfNotes['final'] == 1) & (dfNotes['type_code'] == "plot")]
    minInDecks = min(dfDeck[dfDeck['in decks'] == dfDeck['in decks_byname']]['in decks'])
    minInDecksPlots = min(dfDeckPlots[dfDeckPlots['in decks'] == dfDeckPlots['in decks_byname']]['in decks'])
    dfincludedByName = pd.concat([dfDeck[dfDeck['in decks'] < minInDecks], dfDeckPlots[dfDeckPlots['in decks'] < minInDecksPlots]]).sort_values('in decks', ascending = False, axis = 0)  #Would not have made it. But in sum all Cards with that name are used enough.
    
    #dict
    dictDeck = dfDeck[['identifier', 'in decks']].set_index('identifier').to_dict()['in decks']
    dictDeckPlots = dfDeckPlots[['identifier', 'in decks']].set_index('identifier').to_dict()['in decks']
    dictBanned = dfBanned[['identifier', 'in decks']].set_index('identifier').to_dict()['in decks']
    dictDonotusepack = dfDonotusepack[['identifier', 'in decks']].set_index('identifier').to_dict()['in decks']
    dictAgendas = dfAgendas[['identifier', 'in decks']].set_index('identifier').to_dict()['in decks']
    dictOtherVersions = dfOtherVersions[['identifier', 'in decks']].set_index('identifier').to_dict()['in decks']
    dictOtherRestricted = dfOtherRestricted[['identifier', 'in decks']].set_index('identifier').to_dict()['in decks']
    dictPods = dfPods[['identifier', 'in decks']].set_index('identifier').to_dict()['in decks']
    dictLimiteds = dfLimiteds[['identifier', 'in decks']].set_index('identifier').to_dict()['in decks']
    #Other Cards
    dictPlots = dfPlots[['identifier', 'in decks']].set_index('identifier').to_dict()['in decks']
    dictDrawdeck = dfDrawdeck[['identifier', 'in decks']].set_index('identifier').to_dict()['in decks']
    dictincludedByName = dfincludedByName[['identifier', 'in decks']].set_index('identifier').to_dict()['in decks']

    #str
    strDonotusepack = "**Don't use Cards after Redesigns (% in Decks since release):** " + "  \n"  + "  \n".join([i + "(" + str(int(round(100*dictDonotusepack[i],0))) + "%)" for i in dictDonotusepack.keys()]) + "."
    strBanned = "**Banned Cards (% in Decks since release):** " + "  \n"  + "  \n".join([i + "(" + str(int(round(100*dictBanned[i],0))) + "%)" for i in dictBanned.keys()]) + "."
    strAgendas = "**Agendas (% in Decks since release):** " + "  \n"  + "  \n".join([i[:-2] + "(" + str(int(round(100*dictAgendas[i],0))) + "%)" for i in list(dictAgendas.keys())[0:noteagendas]]) + "."
    strOtherVersions = "**Alternative Versions (% in Decks since release):** " + "  \n"  + "  \n".join([i + "(" + str(int(round(100*dictOtherVersions[i],0))) + "%)" for i in dictOtherVersions.keys()]) + "."
    strOtherRestricted = "**Other Restricted Cards (% in Decks since release):** " + "  \n"  + "  \n".join([i + "(" + str(int(round(100*dictOtherRestricted[i],0))) + "%)" for i in dictOtherRestricted.keys()]) + "."
    strPods = "**Other Pod Cards (% in Decks since release):** " + "  \n"  + "  \n".join([i + "(" + str(int(round(100*dictPods[i],0))) + "%)" for i in dictPods.keys()]) + "."
    strLimiteds = "**Other Limiteds (% in Decks since release):** " + "  \n"  + "  \n".join([i + "(" + str(int(round(100*dictLimiteds[i],0))) + "%)" for i in dictLimiteds.keys()]) + "."
    #Other Cards
    strPlots = "**Other Plots (% in Decks since release):** " + "  \n"  + "  \n".join([i + "(" + str(int(round(100*dictPlots[i],0))) + "%)" for i in list(dictPlots.keys())[0:noteplots]]) + "."
    strDrawdeck = "**Other Cards (% in Decks since release):** " + "  \n"  + "  \n".join([i + "(" + str(int(round(100*dictDrawdeck[i],0))) + "%)" for i in list(dictDrawdeck.keys())[0:notedrawdeck]]) + "."
    strincludedByName = "**Included by Name (% in Decks since release):** " + "  \n"  + "  \n".join([i + "(" + str(int(round(100*dictincludedByName[i],0))) + "%)" for i in dictincludedByName.keys()]) + "."
    #Deck
    strDeck = "**Deck (% in Decks since release):** " + "  \n"  + "  \n".join([i + "(" + str(int(round(100*dictDeck[i],0))) + "%)" for i in dictDeck.keys()]) + "."
    strDeckPlots = "**Plots (% in Decks since release):** " + "  \n"  + "  \n".join([i + "(" + str(int(round(100*dictDeckPlots[i],0))) + "%)" for i in dictDeckPlots.keys()]) + "."
    
    Notes = strAgendas  + "\n" + "\n" +  strDeckPlots  + "\n" + "\n" +  strDeck  + "\n" + "\n" +  strBanned + "\n" + "\n" + strDonotusepack + "\n" + "\n" + strOtherRestricted + "\n" + "\n" + strPods + "\n" + "\n" + strLimiteds + "\n" + "\n" + strincludedByName + "\n" + "\n" + strOtherVersions  + "\n" + "\n" + strPlots + "\n" + "\n" + strDrawdeck
    return Notes


# =============================================================================
# Voreinstellungen
# =============================================================================
# Use the full page instead of a narrow central column
st.set_page_config(page_title=None, page_icon=None, layout="centered", initial_sidebar_state="auto", menu_items=None)
st.markdown("""
<style>
.big-font {
    font-size:60px !important;
}
</style>
""", unsafe_allow_html=True)
 


st.title("Decklist Generator" + "  \n"  + "for A Game of Thrones LCG 2nd Edition")
# =============================================================================
# EINMALIG!!! load Decks, cards, packs, restricted Lists from .json file
# =============================================================================
alldecks = pd.read_json("data/Decks.json")
allcards = pd.read_json("data/AllCards.json", dtype={'code': 'string'})
allpacks = pd.read_json("data/AllPacks.json")
allRL = pd.read_json("data/RestrictedLists.json") 

# ADD 'available' to get releasedate for cards -> further steps more easy
allcards = pd.merge(allcards, allpacks[['code', 'available']], left_on='pack_code', right_on='code', how="left", suffixes=('', '_y'))
allcards.drop(allcards.filter(regex='_y$').columns.tolist(),axis=1, inplace=True)

st.write("based on [https://thronesdb.com](https://thronesdb.com/)" + " latest update: " + str(alldecks.iloc[-1]['date_creation'][0:10]))
# =============================================================================
# Parameter
# =============================================================================
col1, col2 = st.columns(2)
#Deckbase
with col1: strFaction = st.selectbox("Faction", sorted(alldecks['faction_name'].unique())) #"House Targaryen" #Faction name or faction Code??!!!
#st.write("Selected Faction:", strFaction)
with col2: strAgenda = st.selectbox("Agenda", ["All Agendas"] + sorted(allcards[allcards['type_code'] == "agenda"]['name'].unique())) #"Valyrian Steel" #NAME NOT LABEL!!!!!
#st.write("Selected Agenda:", strAgenda)
AndOr = st.radio("Deckselection Rule for 'Cards used'", options = ['AND','OR'])
lstCardlabels = st.multiselect("Cards used", sorted(allcards[allcards['type_code'] != "agenda"]['label'].unique())) #["Missandei"] #23 VS Decks. 22 VS Decks with Missandei
#st.write("Selected Cards:", lstCardlabels)
col3, col4 = st.columns(2)
with col4: factor = st.slider(label="% of latest uploaded Decks", min_value=1, max_value=100, value=33) #33 = Default

#lstNoAgenda = []
#lstNoCardlabels = [] #'"faction_name": "Harrenhal (FFH)"'

# =============================================================================
# laufende Aktualisierungen
# =============================================================================
alldecks = alldecks[int((1-float(factor/100))*len(alldecks)):] # newest X% of the Decks (X=factor)
with col4: st.write("Decks since:", alldecks.iloc[0]['date_creation'][0:10])
alldecks = alldecks[alldecks.apply(lambda row: sum(row['slots'].values()), axis=1) <  111] #only decks with max 110 cards (DRAWDECK+PLOTS!!!)
alldecks = alldecks[alldecks['faction_name'] == strFaction]
if strAgenda != "All Agendas": #Agenda #BY NAME NOT LABEL!
     agenda_code = allcards[allcards['name'] == strAgenda]['code'].tolist()#[x["code"] for x in allcards if x["name"] == strAgenda]
     alldecks = alldecks[alldecks.apply(lambda row: any(x in row["agendas"] for x in agenda_code), axis=1)]
if AndOr == "AND":   
    for strCardlabel in lstCardlabels: #"slots": {"01002": 1, ... }
        curr_code =  allcards[allcards['label'] == strCardlabel].iloc[0]['code'] #[x["code"] for x in allcards if x["label"] == strCardlabel][0]
        alldecks = alldecks[alldecks.apply(lambda row: curr_code in row["slots"].keys(), axis=1)]
elif AndOr == "OR":
    tempalldecks = pd.DataFrame()
    for strCardlabel in lstCardlabels:
        curr_code =  allcards[allcards['label'] == strCardlabel].iloc[0]['code'] #[x["code"] for x in allcards if x["label"] == strCardlabel][0]
        tempalldecks = pd.concat([tempalldecks, alldecks[alldecks.apply(lambda row: curr_code in row["slots"].keys(), axis=1)]])
    alldecks = tempalldecks
with col3: st.info(str(len(alldecks)) + " Decks found." + "  \n" +  "Recommended: <100 (avoid long runtime)") #st.markdown('<p class="big-font">'+ "Decks: " + str(len(alldecks))  + '</p>', unsafe_allow_html=True)
        
# =============================================================================
# weitere Parameter
# =============================================================================
col5, col6 = st.columns(2)
#RL
#lstRLSelection = ["Standard v1.1", "Valyrian v1.0", "FFG FAQ v3.0"]
#with col5: restrictedListTitle = st.selectbox("Restricted List", ["No Restricted List"] + allRL[allRL.title.isin(lstRLSelection)].sort_values('effectiveOn', ascending = False, axis = 0)['title'].tolist()) #"gotstandard1.1" #"gotvalyrian1.0" # With Redesigns (Standard): "gotstandard1.1" - No Redesigns (Valyrian): "gotvalyrian1.0"
with col5: restrictedListTitle = st.selectbox("Restricted List", ["No Restricted List"] + allRL.sort_values('effectiveOn', ascending = False, axis = 0)['title'].tolist()) #"gotstandard1.1" #"gotvalyrian1.0" # With Redesigns (Standard): "gotstandard1.1" - No Redesigns (Valyrian): "gotvalyrian1.0"
with col6: JoustMelee = st.radio("", options = ['joust','melee']) #'joust' #'melee' #
#Cardbase
blAllowAfterRedesigns = not st.checkbox("Don't use Cards after Redesigns")#False 


# =============================================================================
# BUTTON -> CALCULATION
# =============================================================================


if len(alldecks) == 0:
    st.error("NO DECKS FOUND FOR YOUR OPTIONS! (Maybe your options are too specific. Please change your input and look at the Deckcount above.) \n \n The 'Generate Decklist'-Button will appear if at least 1 Deck fits your options.")
else:
    if st.button('Generate Decklist'):
        with st.spinner('In Progress...'):
            my_bar = st.progress(0)
            #Select Cards
            DoNotUsePacks = ["Valyrian Draft Set","Kingsmoot Variant","Hand of the King Variant"]
            if not blAllowAfterRedesigns:
                PacksAfterRedesign = allpacks[allpacks['available'] > allpacks[allpacks['name'] == "Redesigns"].iloc[0]['available']]['name'].tolist()#=[i for i in AllPacks if (date.fromisoformat(releaseRedesign) <= date.fromisoformat(i["available"]))]
                DoNotUsePacks = DoNotUsePacks + PacksAfterRedesign
            relevantcards = allcards #[~allcards.pack_name.isin(DoNotUsePacks)]
            #1 generate Dataframe with List of Cards in Decks
            dfCardsInDecks = GetCardsInDecks(relevantcards,alldecks)
            #st.dataframe(dfCardsInDecks[['label', 'copy', 'in decks']].head())
            #2 trägt Deckbau-Entscheidungen ein 
            # Select Restricted List
            #Redesign-Cards are handled with restricted List (Valyrian or Standard)
            if restrictedListTitle != "No Restricted List":
                RL = allRL[allRL['title'] == restrictedListTitle].iloc[0]['contents'][JoustMelee]
            else:
                RL = {'banned': [], 'restricted': [], 'restricted_pods': []}
            #dict for shorter runtime
            dictCodeType = allcards[['code', 'type_code']].set_index('code').to_dict()['type_code']
            allcards['limited'] = allcards.apply(lambda rowCards: rowCards['text'].find("Limited.") >-1, axis=1)
            dictCodeLimited = allcards[['code', 'limited']].set_index('code').to_dict()['limited']
            #calculate mean
            alldecks['count_plot'] = alldecks.apply(lambda rowDecks: sum([rowDecks['slots'][key] for key in rowDecks['slots'].keys() if dictCodeType[key] == "plot"]), axis=1)
            alldecks['count_drawdeck'] = alldecks.apply(lambda rowDecks: sum([rowDecks['slots'][key] for key in rowDecks['slots'].keys() if dictCodeType[key] != "plot"]), axis=1)
            alldecks['count_character'] = alldecks.apply(lambda rowDecks: sum([rowDecks['slots'][key] for key in rowDecks['slots'].keys() if dictCodeType[key] == "character"]), axis=1)
            alldecks['count_limited'] = alldecks.apply(lambda rowDecks: sum([rowDecks['slots'][key] for key in rowDecks['slots'].keys() if dictCodeLimited[key]]), axis=1)
            dictCountTypes = alldecks[['count_plot', 'count_drawdeck', 'count_character', 'count_limited']].mean().to_dict()
            #get parameters
            totalplots = 7
            meanDrawdeck = round(dictCountTypes['count_drawdeck'])
            if meanDrawdeck >= 88:
                totalcards = 100
            elif meanDrawdeck >= 68:
                totalcards = 75
            else:
                totalcards = 60
            includeCharacters = round(dictCountTypes['count_character'])
            includeLimiteds = round(dictCountTypes['count_limited'])
            #Deckbau Entscheidungen eintragen
            dfFinal = GenerateDecklist(dfCardsInDecks, RL, totalcards, totalplots, includeCharacters, includeLimiteds, DoNotUsePacks)
            
            #3 generiert daraus decklist und Notes
            strDecklist = get_Decklist(dfFinal)
            strNotes = get_Notes(dfFinal)
            #Decklist und Notes ergänzen
            strTitle = "**" + strFaction + "-" + strAgenda + "-" + restrictedListTitle + "-" + JoustMelee + "-{}%".format(factor) + "**"
            strDecklist = strTitle + "\n" + "\n" + strFaction + "\n" + "\n" + (strAgenda if strAgenda != "All Agendas" else "") + "\n" + "\n" + strDecklist 
            strDeckSummary = "Decks: " + str(len(alldecks)) + " (creationdate: " + alldecks.iloc[0]["date_creation"][0:10] +" to "+ alldecks.iloc[-1]["date_creation"][0:10] +")" 
            strFactor = "The latest {}% of all decks on thronesdb.com are taken into account. Excluding decks with more than 110 cards in their drawdeck.".format(factor)
            strSelectionSummary = "**Selection Summary**" + "  \n" + strDeckSummary + "  \n" + "Faction: " + strFaction + "  \n" + "Agenda: " + strAgenda + ("  \n" + "Only Decks which include the following cards: " + (" " + AndOr + " ").join(lstCardlabels) if len(lstCardlabels) != 0 else "") + "  \n" + "Restricted List: " + restrictedListTitle + " " + JoustMelee + "  \n" + ("With Cards after Redesigns" if blAllowAfterRedesigns else "No Cards after Redesigns") + "  \n" + strFactor
            strRemarks =  "Deck Size: " + str(totalcards) + " | Characters: " + str(includeCharacters) + " | Limiteds: " + str(includeLimiteds) + "  \n" + "(chosen by rounded averages.)"
            #"**Remarks:**"   + "  \n" + "  \n" + "Only Cards which are in 3 or more Decks are analyzed."
            strNotes = strSelectionSummary + "  \n"  + strRemarks + "\n" + "\n" + strNotes 
            my_bar.progress(100)
            #Ausgabe
            col7, col8 = st.columns(2)
            with col7:
                st.header("DECKLIST")
                st.download_button(label="Save Decklist as .txt", data=strDecklist.replace("**", ""), file_name=strTitle +'.txt')
                st.markdown(strDecklist)
            with col8:
                st.header("NOTES")
                st.download_button(label="Save Notes as .txt", data=strNotes.replace("**", ""), file_name=strTitle + "(NOTES)" +'.txt')
                st.markdown(strNotes)
            my_bar.empty()
