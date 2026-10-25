from shiny import App, reactive, render, ui, req
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Mapping the codes from the dataset to their actual names.
# I only found a pdf file with this information, so I manually created this dictionary.
# Source: https://www.bag.admin.ch/dam/de/sd-web/tGi8dHtom8eb/Zugelassene%20Krankenversicherer_1.10.2025.pdf
# TODO: There is actually an xlsx file with this information: https://www.bag.admin.ch/dam/de/sd-web/Gjlbd6ULgWmm/Zugelassene%20Krankenversicherer_1.10.2025.xlsx
BAG_VERSICHERER = {
    1560: "Agrisano",
    1507: "AMB Assurances SA",
    32:   "Aquilana",
    1542: "Assura",
    312:  "Atupri",
    343:  "Avenir",
    1322: "Birchmeier",
    290:  "CONCORDIA",
    8:    "CSS",
    881:  "EGK",
    134:  "Einsiedler",
    1386: "GALENOS AG",
    780:  "Glarner",
    1562: "Helsana",
    829:  "KLuG",
    376:  "KPT",
    820:  "Lumneziana",
    360:  "KKLH",
    1479: "Mutuel",
    455:  "ÖKK",
    1535: "Philos",
    1401: "rhenusana",
    1568: "sana24",
    901: "sanavals",
    1509: "Sanitas",
    923: "SLKK",
    941: "sodalis",
    246: "Steffisburg",
    194: "Sumiswalder",
    1384: "SWICA",
    1113: "Vallée d’Entremont",
    1555: "Visana",
    1040: "Visperterminen",
    966: "vita surselva",
    1570: "Vivacare",
    509: "Vivao Sympany",
    1318: "Wädenswil",
}

MAX_AMOUNT_YOU_PAY_AFTER_DEDUCTIBLE = 700
DECIMAL_AFTER_DEDUCTIBLE = 0.10 # We need to pay 10% of costs after deductible
DATA_RETRIEVED_ON = "2025-10-24"

DEDUCTIBLE_CHILD_LVL_TO_AMOUNT = {"FRASTU_01": 0, "FRASTU_02": 100, "FRASTU_03": 200, "FRASTU_04": 300, "FRASTU_05": 400, "FRASTU_06": 500, "FRASTU_07": 600}
DEDUCTIBLE_ADULT_LVL_TO_AMOUNT = {"FRASTU_01": 300, "FRASTU_02": 500, "FRASTU_03": 1000, "FRASTU_04": 1500, "FRASTU_05": 2000, "FRASTU_06": 2500}

def calculate_annual_cost_health_insurance(treatment_costs_during_year, premium_per_month, deductible_amount):
        amount_after_deductible = max(0, treatment_costs_during_year - deductible_amount)
        costs_to_cover_after_deductible = min(amount_after_deductible * DECIMAL_AFTER_DEDUCTIBLE, MAX_AMOUNT_YOU_PAY_AFTER_DEDUCTIBLE)
        total_treatment_costs_to_cover = min(treatment_costs_during_year, deductible_amount) + costs_to_cover_after_deductible
        total_cost = total_treatment_costs_to_cover + 12 * premium_per_month
        return total_cost
    

def calculate_annual_cost_insurance(treatment_costs_during_year, premium_per_month, deductible_amount, percentage_covered, max_amount_insurance_pays):
    # Generally, you will need to pay the following amount (per year) by yourself:
    # 1. premium
    # 2. the difference between the treatment costs and the amount that the insurance pays,
    #    where the amount that the insurance pays is MIN(percentage_covered * amount_after_deductible, max_amount_insurance_pays)
    premium_per_year = 12 * premium_per_month
    amount_after_deductible = max(treatment_costs_during_year - deductible_amount, 0)
    insurance_pays = min(percentage_covered * amount_after_deductible, max_amount_insurance_pays)
    total_costs_you_pay = premium_per_year + (treatment_costs_during_year - insurance_pays)
    return total_costs_you_pay


def load_app_data():
    """Load the datasets required by the application."""
    try:
        premiums = pd.read_csv("data/premiums.csv", sep=",")
        premiums['Versicherung'] = premiums['Versicherer'].map(BAG_VERSICHERER)

        premium_regions = pd.read_excel("data/premium_regions.xlsx", sheet_name='A_COM', skiprows=4,engine="openpyxl")

        insurance_model_restrictions = pd.read_csv("data/insurance_model_restrictions.csv", sep=",")

        # We only need the rows where there is a restriction
        insurance_model_restrictions = insurance_model_restrictions[insurance_model_restrictions["Eingeschränkt"] == "Y"]
        # Convert the "Gemeinden-BFS" column from comma-separated strings to lists of integers
        insurance_model_restrictions["Gemeinden-BFS"] = insurance_model_restrictions["Gemeinden-BFS"].apply(lambda x: [int(i) for i in x.split(",")] if pd.notna(x) else x)
        # The original excel file has column names on two lines: First Line = German name, Second Line = French translation
        premium_regions.columns = [col.splitlines()[0] for col in premium_regions.columns]
        print("Loaded data successfully.")
        print(premiums.head())
        print(premium_regions.head())
        print(insurance_model_restrictions.head())

    except Exception as e:
        raise RuntimeError(
                "Could not load the required application data."
            ) from e

    if premiums.empty or premium_regions.empty or insurance_model_restrictions.empty:
        raise RuntimeError("One or more application datasets are empty.")

    return premiums, premium_regions, insurance_model_restrictions

premiums, premium_regions, insurance_model_restrictions = load_app_data()

# Calculate count of each PLZ and append as a new column
premium_regions['plz_count'] = premium_regions.groupby('PLZ')['PLZ'].transform('count')

municipality_choices = {'': ''} | {f"{row['BFS-Nr.']}|{row['Kanton']}|{row['Region']}|{row['PLZ']}|{row['Ort']}|{row['Gemeinde']}": f"{row['PLZ']} {row['Ort']}" + (f" (Gemeinde {row['Gemeinde']})" if row['plz_count'] > 1 else "")
                for _, row in premium_regions.iterrows()}

app_ui = ui.page_fixed(
    ui.panel_title(
        ui.h2(
            "Swiss Health Insurance Premium Calculator for 2026",
            class_="pt-4 pb-3",
        )
    ),
    ui.output_ui("dynamic_page"),
    ui.tags.footer(
        ui.hr(),
        ui.p(
            "Data: ",
            ui.a(
                "Federal Office of Public Health (FOPH/BAG)",
                href="https://opendata.swiss/en/dataset/health-insurance-premiums",
                target="_blank",
                rel="noopener noreferrer",
            ),
            f" | Retrieved {DATA_RETRIEVED_ON}",
        ),
        ui.p(
            "Unofficial comparison tool. Verify premiums and availability "
            "with the insurer before making a decision."
        ),
        class_="text-muted small pb-4",
    ),
)
        
def server(input, output, session):
    page_state = reactive.Value('input_insurance_calculation')
    selectize_updated = reactive.Value(False)

    # Store whether user has tried to calculate offers (to show validation errors)
    calculation_attempted = reactive.Value(False)
    personal_details = reactive.Value({
        "birth_year": None,
        "location": None,
        "deductible": None,
        "accident_insurance": None
    })

    # TODO: Decrease size of the UI elements to reduce vertical scrolling ...
    @output
    @render.ui
    def dynamic_page():
        if page_state() == 'input_insurance_calculation':
            previous_inputs = personal_details.get()
            selectize_updated.set(False)
            return ui.card(
                ui.p("Please enter your personal details to calculate health insurance offers for 2027."),
                ui.input_numeric("birth_year", "Year of birth", value=previous_inputs.get('birth_year'), min=1900, max=2026, step=1),
                ui.output_ui("municipality_select"),
                ui.output_ui("deductible_select"),
                ui.input_radio_buttons(
                    "accident_insurance",
                    "Include accident insurance?",
                    choices={"MIT_UNF": "Yes", "OHN_UNF": "No"},
                    selected=previous_inputs.get('accident_insurance')
                ),
                ui.input_action_button("calculate_offers", "Calculate Insurance Offers"),
                ui.output_ui("input_errors_display")
            )
        elif page_state() == 'results':
            personal_details_locked = personal_details.get()
            return ui.card(
                ui.h4("Entered Personal Details"),
                ui.p(f"Year of birth: {personal_details_locked['birth_year']}"),
                ui.p(f"Municipality: {location_display()}"),
                ui.p(f"Deductible: {deductible_display()}"),
                ui.p(f"Accident insurance: {accident_display()}"),
                ui.input_action_button("modify_details", "Modify"),
                ui.card_header("Insurance Cost Comparison"),
                ui.output_data_frame("insurance_table"),
                ui.output_plot("deductibles_comparison_plot"),
                ui.output_data_frame("calculate_annual_cost_table")
            )
        
        elif page_state() == 'general_insurance_calculation':
            return ui.card(
                ui.input_text("insurance_name", "Insurance name", value=""),
                ui.input_numeric("premium_per_month", "Premium per month (CHF)", value=0, min=0, step=0.1),
                ui.input_numeric("deductible_amount", "Deductible amount (CHF)", value=0, min=0, step=50),
                ui.input_numeric("percentage_covered", "Covered by insurance (%)", value=50, min=0, max=100, step=5),
                ui.input_numeric("treatment_costs_during_year", "Treatment costs during year (CHF)", value=0, min=0, step=50),
            )

        
    @reactive.calc
    def get_input_errors():
        errors = []
        if not age_validation():
            errors.append("Please enter a valid birth year between 1900 and 2026 and then choose a deductible level.")
        if not input.location():
            errors.append("Please select a municipality.")
        if not input.accident_insurance():
            errors.append("Please select whether to include accident insurance.")
        return errors


    # When user clicks "Calculate Offers", switch to results view
    @reactive.Effect
    @reactive.event(input.calculate_offers)
    def _():
        errors = get_input_errors()
        calculation_attempted.set(True)
        if len(errors) == 0:
            personal_details.set({
                "birth_year": input.birth_year(),
                "location": input.location(),
                "deductible": input.deductible(),
                "accident_insurance": input.accident_insurance()
            })
            page_state.set("results")

    @render.ui
    def input_errors_display():
        errors = get_input_errors()
        if calculation_attempted() and len(errors) > 0:
            return ui.div(
                ui.tags.div(
                    ui.tags.strong("Please fix the following errors:"),
                    ui.tags.ul([ui.tags.li(error) for error in errors]),
                    class_="alert alert-danger",
                    role="alert"
                )
            )
        else:
            return ui.div()
        
    @reactive.Effect
    @reactive.event(input.modify_details)
    def _():
        page_state.set("input_insurance_calculation")
        calculation_attempted.set(False)

    @reactive.calc
    def is_child():
        return personal_details.get()['birth_year'] >= 2009

    @reactive.calc
    def age_category():
        if is_child():
            return 'AKA_01_KIN'
        elif input.birth_year() >= 2002:
            return 'AKA_02_JUG'
        else:
            return 'AKA_03_ERW'
        
    @reactive.calc
    def deductible_display():
        return f"{deductible_amount()} CHF"
    
    @reactive.calc
    def deductible_amount():
        deductible_lvl = personal_details.get()['deductible']
        return DEDUCTIBLE_CHILD_LVL_TO_AMOUNT[deductible_lvl] if is_child() else DEDUCTIBLE_ADULT_LVL_TO_AMOUNT[deductible_lvl]
    
    def deductible_amount_for_person(deductible_level, age_class):
        return DEDUCTIBLE_CHILD_LVL_TO_AMOUNT[deductible_level] if age_class == 'AKA_01_KIN' else DEDUCTIBLE_ADULT_LVL_TO_AMOUNT[deductible_level]

    @reactive.calc
    def location_display():
        loc_code = personal_details.get()['location']
        return municipality_choices[loc_code]
    
    @reactive.calc
    def accident_display():
        return "Yes" if personal_details.get()['accident_insurance'] == "MIT_UNF" else "No"

    @render.ui
    def municipality_select():
        selectize_ui = ui.input_selectize(
            "location",
            "Enter Postal Code or Municipality",
            choices=[],   # Empty at first load because we will update it later for much faster performance.
            options={"allowEmptyOption": True, "showEmptyOptionInDropdown": False},
            selected="",
        )
        return selectize_ui

    # Update location selection choices after the UI is rendered. This way is much faster.
    @reactive.effect
    def _update_selectize_choices():
        # Update selectize choices after the UI is rendered
        previous_inputs = personal_details.get()
        previous_location = previous_inputs.get('location') if previous_inputs else None
        # Only update when we're on the input page and the location selection box exists.
        if page_state() == 'input_insurance_calculation' and ('location' in session.input) and not selectize_updated():
            ui.update_selectize(
                "location",
                choices=municipality_choices,
                server=True,
                session=session,
                selected=previous_location # Restore the previous selection
            )
            selectize_updated.set(True)
    
    @reactive.calc
    def age_validation():
        birth_year = input.birth_year()
        return birth_year is not None and isinstance(birth_year, int) and 1900 <= birth_year <= 2026

    @render.ui
    def deductible_select():
        birth_year = input.birth_year()
        if not age_validation():
            # If the age is not set properly, disable the deductible selection
            return ui.div(
                ui.tags.label("Deductible", class_="form-label"),
                ui.tags.select(
                    disabled=True,
                    title="Please enter your birth year.",
                    class_="form-select",
                    style="opacity: 0.6;"
                ),
                class_="form-group shiny-input-container"
                ) 
        deductible_options = DEDUCTIBLE_ADULT_LVL_TO_AMOUNT if birth_year < 2009 else DEDUCTIBLE_CHILD_LVL_TO_AMOUNT
        
        previous_inputs = personal_details.get()
        previous_deductible = previous_inputs.get('deductible') if previous_inputs else None
        return ui.input_select(
            "deductible",
            "Deductible",
            choices=deductible_options,
            selected=previous_deductible
        )
    

    # Filter all insurance offers based on the inputs
    @reactive.event(input.calculate_offers)
    def calculate_data():
        req(len(get_input_errors()) == 0) # Only run the calculation once there are no input errors.
        df = pd.DataFrame()
        bfs_nr, canton, region, *_, = input.location().split('|')
        bfs_nr = int(bfs_nr)

        df = premiums[(premiums['Kanton'] == canton) & 
                           (premiums['Region'] == f"PR_REG_{region}") & 
                           (premiums['Altersklasse'] == age_category()) &
                           (premiums['Franchisestufe'] == input.deductible()) &
                           (premiums['Unfalleinschluss'] == input.accident_insurance())].sort_values(by='Prämie')
        
        join_keys = ['Kanton', 'Region', 'Versicherer', 'Tarif', 'Tariftyp']
        merged = pd.merge(df, insurance_model_restrictions[join_keys + ['Gemeinden-BFS']], on=join_keys, how='left')
        
        # Filter out rows where there is a restriction for the selected municipality (BFS-Nr.)
        filtered = merged[(merged['Gemeinden-BFS'].isna()) | (merged['Gemeinden-BFS'].apply(lambda x: bfs_nr in x if isinstance(x, list) else False))]  
        
        return filtered.drop(columns=['Gemeinden-BFS'])


    @render.data_frame
    def insurance_table():
        return render.DataGrid(
            calculate_data()[['Versicherung', 'Tarifbezeichnung', 'Prämie']], 
            selection_mode="row"
        )
    
    # Create a plot comparing different deductible levels for the selected insurance plan.
    # This allows you to visually see what deductible level is best for what treatment costs.
    @render.plot
    def deductibles_comparison_plot():
        selected = input.insurance_table_selected_rows()

        if not selected:
            return None
        
        df = calculate_data()
        row = df.iloc[selected[0]]
        insurance_provider, insurance_plan = row['Versicherung'], row['Tarifbezeichnung']

        deductible_levels_to_compare = premiums[
            (premiums['Versicherung'] == insurance_provider) &
            (premiums['Tarifbezeichnung'] == insurance_plan) &
            (premiums['Unfalleinschluss'] == row['Unfalleinschluss']) &
            (premiums['Kanton'] == row['Kanton']) &
            (premiums['Region'] == row['Region']) &
            (premiums['Altersklasse'] == row['Altersklasse'])
        ]

        # Create treatment costs range (0 to 10,000 CHF)
        treatment_costs = np.linspace(0, 10000, 1000)

        fig, ax = plt.subplots(figsize=(8, 5))


        for _, deductible_row in deductible_levels_to_compare.iterrows():    
            premium_amount = deductible_row['Prämie']
            deductible_amount = deductible_amount_for_person(deductible_row['Franchisestufe'], row['Altersklasse'])
            annual_costs = np.array([
                calculate_annual_cost_health_insurance(treatment_costs_during_year=x, premium_per_month=premium_amount, deductible_amount=deductible_amount)
                for x in treatment_costs
            ])

            ax.plot(treatment_costs, annual_costs, label=f'{deductible_amount} CHF Deductible')

        ax.set_xlabel('Treatment Costs (CHF)')
        ax.set_ylabel('Total Costs for You (CHF)')
        ax.set_title(f'Annual Total Costs for You: {insurance_provider} - {insurance_plan}')
        ax.legend()
        ax.grid(True)

        return fig

    @render.data_frame
    def calculate_annual_cost_table():
        treatment_costs = [0, 300, 500, 1000, 1500, 2000, 3000, 5000, 10000]

        selected = input.insurance_table_selected_rows()

        if not selected:
            return None
        
        df = calculate_data()
        row = df.iloc[selected[0]]
        insurance_provider, insurance_plan = row['Versicherung'], row['Tarifbezeichnung']

        deductible_levels_to_compare = premiums[
            (premiums['Versicherung'] == insurance_provider) &
            (premiums['Tarifbezeichnung'] == insurance_plan) &
            (premiums['Unfalleinschluss'] == row['Unfalleinschluss']) &
            (premiums['Kanton'] == row['Kanton']) &
            (premiums['Region'] == row['Region']) &
            (premiums['Altersklasse'] == row['Altersklasse'])
        ]

        result_df = pd.DataFrame({"Treatment Costs during the year": [f"{treatment_cost} CHF" for treatment_cost in treatment_costs]})
        for _, deductible_row in deductible_levels_to_compare.iterrows():    
            premium_amount = deductible_row['Prämie']
            deductible_amount = deductible_amount_for_person(deductible_row['Franchisestufe'], row['Altersklasse'])
            result_df[f"{deductible_amount} CHF Deductible"] = [f"{calculate_annual_cost_health_insurance(treatment_costs_during_year=treatment_cost, premium_per_month=premium_amount, deductible_amount=deductible_amount):.2f} CHF" for treatment_cost in treatment_costs]

        return result_df

    
app = App(app_ui, server)
