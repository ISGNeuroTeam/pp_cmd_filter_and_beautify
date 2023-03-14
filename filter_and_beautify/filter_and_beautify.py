from upstream.potentials.Economics import Economics


def beautify_result_df(df):
    def swap_start_end(row):
        if not row["startIsSource"] and row["X_kg_sec"] < 0:
            return row["node_name_end"], row["node_name_start"]
        else:
            return row["node_name_start"], row["node_name_end"]

    def make_positive(row, colname):
        return row[colname] if row["startIsSource"] else abs(row[colname])

    def make_flow_positive(row):
        return make_positive(row, "X_kg_sec")

    def make_velocity_positive(row):
        return make_positive(row, "velocity_m_sec")

    def convert_flow_to_m3_day(row):
        density = (
            row["density_calc"] * 1000
            if "density_calc" in row
            else row["res_liquid_density_kg_m3"]
        )
        return row["X_kg_sec"] * 86400 / density

    df[["node_name_start", "node_name_end"]] = df.apply(
        swap_start_end, axis=1, result_type="expand"
    )
    df["X_kg_sec"] = df.apply(make_flow_positive, axis=1)
    df["X_m3_day"] = df.apply(convert_flow_to_m3_day, axis=1)
    df["velocity_m_sec"] = df.apply(make_velocity_positive, axis=1)
    return df


def get_oil_debit(row):
    init_q = row["shtr_debit"]
    init_qn = row["shtr_oil_debit"]
    init_water = row["VolumeWater"]
    oil_volume_rate = (100 - init_water) / 100
    q = row["X_m3_day"]
    oil_density = init_qn / (init_q * oil_volume_rate)
    return oil_density * q * oil_volume_rate


def calculate_fcf(
        row,
        params,
        q_col="shtr_debit",
        qn_col="shtr_oil_debit",
        density_col="density_calc",
        ure_col="URE",
):
    economics = Economics(
        q_zh_vol=row[q_col],
        ro_sm=row[density_col],
        q_n=row[qn_col],
        specific_energy_mp=row[ure_col],
        **params,
    )
    return economics.get_FCF()


def add_new_fcf(df, _params):
    df["Qn_new"] = df.apply(lambda row: get_oil_debit(row), axis=1)
    df["URE_new"] = (
            24 * df["res_pump_power_watt"] / (1000 * df["X_m3_day"] * df["density_calc"])
    )
    df["URE_new"] = df["URE_new"].fillna(df["URE"])
    df["FCF_new"] = df.apply(
        lambda x: calculate_fcf(
            x, _params, q_col="X_m3_day", qn_col="Qn_new", ure_col="URE_new"
        ),
        axis=1,
    )
    return df


def filter_and_beautify(df, params):
    wells_mask = df["juncType"] == "wellpump"
    pipes_q_mask = (df["juncType"] == "pipe") & (df["startKind"] == "Q")
    result_wells_mask = wells_mask | pipes_q_mask
    pretty_df = beautify_result_df(df[result_wells_mask])
    pretty_df = add_new_fcf(pretty_df, params)
    return pretty_df
