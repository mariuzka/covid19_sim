set more off

* set the working directory to the folder of this do-file
chdir "..."

* load data
use "data\soep4sim\merged_soep_datasets.dta" , replace

* use data from 2017
keep if syear == 2017

* age
replace age = . if age < 0 | age > 100
tab age, mi

* work hours
tab work_hours_week, mi
recode work_hours_week (-5 -3 -2 -1 = .)

replace work_hours_week = 0 if missing(work_hours_week) & work_hours_year == 0 // 0 eintragen, wenn fehlend und auf ander Arbeitsstunden-Variable 0
replace work_hours_week = 0 if missing(work_hours_week) & age > 65 // 0 eintragen, wenn fehlend und älter als 65
replace work_hours_week = 0 if age < 20 // 0 eintragen, wenn jünger als 20


tab work_hours_week, mi
* 1888 Fälle (3,53%) fehlend, die im Folgenden mit Mittelwertimputation ersetzt werden

egen age_gender_whw_mean = mean(work_hours_week), by(age gender) // Arbeitsstunden-Mittelwert nach Alter und Geschlecht berechnen
replace work_hours_week = age_gender_whw_mean if missing(work_hours_week) // Alle fehlenden Arbeitsstunden-Werte durch Mittelwert ersetzen
generate computed_work_hours_day = work_hours_week / 5 // wöchentliche Arbeitsstunden auf 5 Arbeitsstage verteilen

tab work_hours_week, mi

* student
rename bhp_16_02 uni
tab uni, mi
gen student = 0
replace student = 1 if uni > 0 & uni <= 5
tab age student, mi

* shopping hours
* missing values are replaced by the average
tab hours_shopping, mi

recode hours_shopping (-5 -3 -2 = .)
egen hours_shopping_mi = mean(hours_shopping)
replace hours_shopping_mi = hours_shopping if hours_shopping != .

tab hours_shopping_mi, mi
* 26,916% bekommen den Mittelwert von ca. 1h eingesetzt (hier sind allerdings auch noch die Kinder mitgerechnet, die in der Simulation dann gar nicht einkaufen gehen)

* recode NACE2
rename pgnace2 nace2
replace nace2 = 0 if nace2 == . | nace2 < 0

tab nace2

replace nace2 = -1 if nace2 == 0 & computed_work_hours_day == 0

tab nace2
* es bleiben am Ende 1850 Personen (3.46%) übrig, die regulär arbeiten müssten, aber keiner NACE2-Kategorie zugeordnet werden können
* Umgang mit diesen: Diese werden in jedem Simulationsdurchlauf in der Funktion "create_soep_population" zufällig einer Nace2-Kategorie zugewiesen

gen nace2_short = nace2
recode nace2_short ///
(1/3 = 1) ///
(5/9 = 2) ///
(10/33 = 3) ///
(35 = 4) ///
(36/39 = 5) ///
(41/43 = 6) ///
(45/47 = 7) ///
(49/53 = 8) ///
(55/56 = 9) ///
(58/63 = 10) ///
(64/66 = 11) ///
(68 = 12) ///
(69/75 = 13) ///
(77/82 = 14) ///
(84 = 15) ///
(85 = 16) ///
(86/88 = 17) ///
(90/93 = 18) ///
(94/96 = 19) ///
(97/98 = 20) ///
(99 = 21)

* drop non-relevent variables
keep pid hid federal_state computed_work_hours_day age gender nace2 nace2_short student hours_shopping_mi bhhhrf

* check individuals for missings
gen data_is_complete = 1
replace data_is_complete = 0 if missing(computed_work_hours_day, age, gender, student, hours_shopping_mi, nace2, nace2_short)

* check household for missings
* set variable to 0 if one of the household member has missing data
egen household_data_is_complete = min(data_is_complete), by(hid)

tab household_data_is_complete
* Bei 869 Fällen (1,62%) gibt es Missings im Haushalt, sodass diese Personen ausgeschlossen werden

* drop all households with missing data
keep if household_data_is_complete

* save dataset
export delimited using "data\soep4sim\soep_for_corona_simulation.csv", nolabel quote replace
