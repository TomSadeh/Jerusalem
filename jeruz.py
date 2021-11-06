import pandas as pd
import numpy as np
from scipy.stats.mstats import gmean
import matplotlib.pyplot as plt

def compute_tax(salary, levels, pcts, zichuy = 2.25, schum_zichuy = 219, max_salary = 0, max_tax = 0):
    """
    A function that calculates the amount of Income Tax or National Security Tax
    a person needs to pay according to the Israeli tax laws.

    Parameters
    ----------
    salary : Float
        The salary from which the tax will be deducted.
    levels : Iterable
        A list of the tax brackets.
    pcts : Iterable
        A list of the tax brackets percents.
    zichuy : Float, optional
        The amount of zichuy points the salary earner has. The default is 2.25.
    schum_zichuy : Int, optional
        The Value of a single zichuy point. The default is 219.
    max_salary : Float, optional
        An optional maximum salary. The default is 0.
    max_tax : Float, optional
        An optional maximum tax. The default is 0.

    Returns
    -------
    Float
        The amount of tax which will be deducted from the salary.
        
    Required libraries
    ---------
    None.    
    """  
    #Returning the max tax if the conditions are met.
    tax = 0 
    if max_tax > 0 and max_salary > 0 and salary >= max_salary:
        return max_tax
    
    #The loop which calculates the tax.    
    for pct, bottom, top in zip(pcts, levels, levels[1:] + [salary]): 
        if salary - bottom <= 0 : 
            break 
        if salary > top:
            tax += pct * (top - bottom)  
        else: 
            tax += pct * (salary - bottom)
   
    #If the tax is less than the tax credit then return zero.     
    if tax <= (zichuy * schum_zichuy):
        return 0
    
    #If not, return the tax minus the tax credit.
    else:
        return tax - (zichuy * schum_zichuy)

def invert(string):
    """
    A function which invert a string.
    Parameters
    ----------
    string : string
        the string to invert.

    Returns
    -------
    string
        An inverted string.

    Required libraries
    ------------------
    None.
    """
    return string[::-1]

#The tax data for the BTL employer tax calcultaions.
levels = [0, 5944]
pcts = [0.0345, 0.075]

#Importing a file with the names of the folders and files for the main loop/
file_names = pd.read_csv(r'')
results = pd.DataFrame()

#Importing PPI and CPI data files.
ppi = pd.read_csv(r'C:\Users\dtsj8\OneDrive\Documents\Work\GNI project\ppi.csv', index_col = 'Year')
cpi = pd.read_csv(r'C:\Users\dtsj8\OneDrive\Documents\Work\GNI project\cpi.csv', index_col = 'Year')

#A flag for including only jews in the calculations.
flag_jews = False
base_address = r''
#The main loop.
for year, folder, file_mbs, file_prat, file_tax in zip(np.arange(2008,2019), file_names.loc[3:,'Folder Address'], file_names.loc[3:,'MB'], file_names.loc[3:,'Prat'], file_names.loc[3:,'Taxes']):
    #Importing the data for each year.
    taxes = pd.read_csv(base_address + '\\' + folder + '\\' + file_tax + '.csv', index_col = 'MisparMB')
    weights = pd.read_csv(base_address + '\\' + folder + '\\' + file_mbs + '.csv', index_col = 'misparmb')
    prat = pd.read_csv(base_address + '\\' + folder + '\\' + file_prat + '.csv')
    taxes.sort_index(inplace = True)
    #Calculating BTL employer tax and pension contribution fee.
    prat['btl maasik'] = prat['i111prat'].apply(compute_tax, args = (levels, pcts), zichuy = 0, max_salary = 43370, max_tax = 3012)
    prat['new i111prat'] = prat[['i111prat', 'btl maasik']].sum(axis = 1) + prat['i111prat'] * 0.125
    
    #Renaming some of the columns for easier data manipulation.
    if 'mishkal' in weights.columns:
        weights.rename(columns = {'mishkal' : 'weight'}, inplace = True)
    if 'dat' in weights.columns or 'nationality' in weights.columns:
        weights.rename(columns = {'dat' : 'Nationality',
                                  'nationality' : 'Nationality'},
                                   inplace = True)
    #Including only Jews in the calculations if the flag is True.
    #Saving the relevant columns in a new DataFrame.
    if flag_jews == False:    
        income = taxes[['i11', 'i111', 'i112', 'i113', 'i12', 'i13', 'i143', 'i144']].copy()
        income = pd.concat([income, weights[['weight', 'yshuv', 'nefashot']]], axis = 1)
        income['new i111'] = prat.groupby('misparMb').agg(np.sum).loc[:, 'new i111prat'].copy()
        
    #Saving the relevant columns in a new DataFrame for 2012 and 2013, which have different nationality coding.
    elif year in [2012,2013]:
        mask = weights['Nationality'] == 0
        income = taxes.loc[mask, ['i11', 'i111', 'i112', 'i113', 'i12', 'i13', 'i143', 'i144']].copy()
        income = pd.concat([income, weights.loc[mask, ['weight', 'yshuv', 'nefashot']]], axis = 1)
        income['new i111'] = prat.groupby('misparMb').agg(np.sum).loc[mask, 'new i111prat'].copy()
    #Saving the relevant columns for the rest of the years.
    else:
        mask = weights['Nationality'].isin([0,1])
        income = taxes.loc[mask, ['i11', 'i111', 'i112', 'i113', 'i12', 'i13', 'i143', 'i144']].copy()
        income = pd.concat([income, weights.loc[mask, ['weight', 'yshuv', 'nefashot']]], axis = 1)
        income['new i111'] = prat.groupby('misparMb').agg(np.sum).loc[mask, 'new i111prat'].copy()
        
    #Calculating the imputed GNI and total wages of israel. 
    income['gni imputed'] = income[['new i111', 'i112', 'i113', 'i12', 'i13', 'i143', 'i144']].sum(axis = 1)
    income['wage imputed'] = income[['new i111']].sum(axis = 1)
    
    #Defining a dictionary with Jerusalem, Tel Aviv and Israel DataFrames.
    cities = {'Jerusalem' : income[income['yshuv'] == 3000].copy(),
              'Tel Aviv' : income[income['yshuv'] == 5000].copy(),
              'Israel' : income}
    
    #The loop that calculates the different items: GNI, GNI per capita, wages, wages per capita, etc.
    for city in cities:
        results.loc[year, city + ' GNI'] = np.sum(cities[city]['gni imputed'] * cities[city]['weight']) * 12
        results.loc[year, city + ' real GNI'] = results.loc[year, city + ' GNI'] / ppi.loc[year, 'PPI'] * 100
        results.loc[year, city + ' Total Wage'] = np.sum(cities[city]['wage imputed'] * cities[city]['weight']) * 12
        results.loc[year, city + ' real Total Wage'] = results.loc[year, city + ' Total Wage'] / cpi.loc[year, 'Average'] * 100
        results.loc[year, city + ' weight'] = cities[city]['weight'].sum()
        results.loc[year, city + ' Capita'] = np.sum(cities[city]['weight'] * cities[city]['nefashot'])
        results.loc[year, city + ' GNI per Capita'] = results.loc[year, city + ' GNI'] / results.loc[year, city + ' Capita']
        results.loc[year, city + ' real GNI per Capita'] = results.loc[year, city + ' GNI per Capita'] / cpi.loc[year, 'Average'] * 100
        results.loc[year, city + ' Wage per Capita'] = results.loc[year, city + ' Total Wage'] / results.loc[year, city + ' Capita']
        results.loc[year, city + ' real Wage per Capita'] = results.loc[year, city + ' Wage per Capita'] / cpi.loc[year, 'Average'] * 100
        results.loc[year, city + ' GNI per Capita real index'] = results.loc[year, city + ' real GNI per Capita'] / results.loc[2008, city + ' real GNI per Capita'] * 100
        results.loc[year, city + ' Wage per Capita real index'] = results.loc[year, city + ' real Wage per Capita'] / results.loc[2008, city + ' real Wage per Capita'] * 100
 
#Calculating percent change and printing it's average.
for city in cities:    
    results[city + ' GNIPC pct change'] = results[city + ' real GNI per Capita'].pct_change() + 1
    results[city + ' WagePC pct change'] = results[city + ' real Wage per Capita'].pct_change() + 1
    print(city + ' GNI per Capita real change: ' + str(np.round(gmean(np.array(results.loc[2009:,city + ' GNIPC pct change'])), 3)))
    print(city + ' Wage Per Capita real change: ' + str(np.round(gmean(np.array(results.loc[2009:,city + ' WagePC pct change'])), 3)))

#Creating the plot.
y = list(np.arange(40000,200000, step = 20000))
ylabels = [f'{label:,}' for label in y]
labels = [invert('ירושלים'), invert('תל אביב'), invert('ישראל')]

plt.figure(figsize = (10,5), dpi = 500)
for city, label in zip(cities, labels):
    plt.plot(results.index, results[city + ' real GNI per Capita'], label = label)
    plt.annotate('+' + str(np.round(results.loc[2018, city + ' GNI per Capita real index'] - 100, 2)) + '%', (2017.6,results.loc[2018, city + ' real GNI per Capita'] - 10000))
plt.title(invert('תל"ג לנפש בישראל, תל אביב וירושלים, 8002-8102'))
plt.ylabel(invert('תל"ג לנפש במחירי 5102'))
plt.xlabel(invert('שנה'))
plt.xticks(np.arange(2008,2019))
plt.yticks(y, ylabels)
plt.text(2007, 15000,invert('מקור: חישובים לפי סקר הכנסות והוצאות של הלמ"ס 8002-8102'))
plt.text(2018, 15000, '@tom_sadeh')
plt.legend()