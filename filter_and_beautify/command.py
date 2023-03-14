import pandas as pd
from otlang.sdk.syntax import Keyword, Positional, OTLType
from pp_exec_env.base_command import BaseCommand, Syntax
from .filter_and_beautify import filter_and_beautify


class FilterAndBeautifyCommand(BaseCommand):
    # define syntax of your command here
    syntax = Syntax(
        [
            Keyword("params", otl_type=OTLType.ALL, inf=True),
        ],
    )
    use_timewindow = False  # Does not require time window arguments
    idempotent = True  # Does not invalidate cache

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        self.log_progress('Start filter_and_beautify command')
        # that is how you get arguments
        params = {k.key: k.value for k in self.get_iter("params")}

        # Make your logic here
        df = filter_and_beautify(df, params)

        return df
