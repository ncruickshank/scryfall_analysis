# packages
from collections import defaultdict
import numpy as np
import pandas as pd

# class
class KindredColorSplits():
    """
    Description
    ----------
    This class contains the methods to extract aggregate statistics 
    for color splits across all tribes. The intention here is to 
    determine which tribes are most evenly balanced.

    Inputs
    ---------
    None
    """
    def __init__(self):
        super().__init__()

        # objects for later use
        self.colors = ['W', 'U', 'B', 'R', 'G']

    # === Main Methods ===

    def define_aggregate_counts(self, data, min_creature_count:int = 20, verbose:bool = True):
        """
        Description
        -----------
        This method creates the counts of colors by tribe
        NOTE that Morophon the Boundless cares about "cards" not "creatures"
        of a specific type. However, since non-creature kindred cards are
        quite rare, we can omit those from this analysis.

        Inputs
        ----------
        data = A list of dictionaries containing our scryfall data
            (from the Scryfall class).
        min_creature_count = The minimum number of creatures we want to 
            include in our final dataset
        verbose = If true, prints useful intermediates

        Returns
        ----------
        None, but self.data will be populated as a pandas dataframe with 
        Cols = ['tribe', 'creature_count', 'avg_mv', 'avg_split', 'std_split', 'white_split', 
            'blue_split', 'black_split', 'red_split', 'green_split']
        Rows = One per tribe with creature_count >= `min_creature_count`
        """
        # === create tribe_stats container ===
        tribe_stats = defaultdict(lambda: {
            'W': 0, 'U': 0, 'B': 0, 'R': 0, 'G': 0,
            'unique_creatures': set(), 'total_mv': 0
        })

        # === populate tribe stats container ===
        for card in data:
            if 'Creature' not in card.get('type_line', ''):
                continue # # skip past non-Creatures

            # NOTE the separator is an emdash, not a regular dash
            subtypes = card.get('type_line', '').split('—', maxsplit = 1)
            if len(subtypes) < 2:
                continue # ex: "Instant" or "Sorcery"
            
            # get creature types
            types = subtypes[1].strip().split(' ')
            
            # color identity from mana cost only
            cost = card.get('mana_cost', '')
            colors = []
            for c in self.colors:
                if c in cost:
                    colors.append(c)

            if not colors:
                continue # skip purely colorless cards

            # store relevant objects
            for t in types:
                key = t.lower()
                tribe_stats[key]['unique_creatures'].add(card['id'])
                tribe_stats[key]['total_mv'] += card.get('cmc', '')
                for c in colors:
                    tribe_stats[key][c] += 1

        # === clean up results ===
        i = 0
        results = []
        for tribe, stats in tribe_stats.items():
            if len(stats['unique_creatures']) < min_creature_count:
                continue # filter out extremely rare tribes

            ## calculate splits
            total = sum(stats[c] for c in self.colors)
            splits = {}
            for c in self.colors:
                x = stats[c] / total
                splits[c] = x

            ## calculate split summaries
            split_mean = np.mean(list(splits.values()))
            split_std = np.std(list(splits.values()))

            ## define and store out the output
            out = {
                'tribe': tribe,
                'creature_count': len(stats['unique_creatures']),
                'avg_mv': round(stats['total_mv'] / len(stats['unique_creatures']), 1),
                'avg_split': split_mean,
                'std_split': split_std,
                'white_split': round(splits['W'] * 100, 2),
                'blue_split': round(splits['U'] * 100, 2),
                'black_split': round(splits['B'] * 100, 2),
                'red_split': round(splits['R'] * 100, 2),
                'green_split': round(splits['G'] * 100, 2)
            }
            results.append(out)

        # create output and store
        self.data = pd.DataFrame(results)\
            .sort_values(by = 'tribe')\
            .reset_index(drop = True)
        del tribe_stats, results

        if verbose:
            print('Kindred Color Split Stats')
            print(f'\tShape = {self.data.shape}\n\tColumns = {self.data.columns.tolist()}')

    def retrieve_top_k_tribes(self, top_k:int = 10, save_data:bool = True):
        """
        Description
        ----------
        This method retrieves the `top_k` tribes based on `std_split`

        Inputs
        ---------
        top_k = The number of tribes we want to return
        save_data = If true, saves to the reports/ folder

        Returns
        ----------
        df = A pandas dataframe containing the top k tribes
        """
        # trim the data of unneeded creature types
        non_tribes = ['//', '—', 'instant', 'sorcery', 'adventure']
        df = self.data.copy()
        df = df[~df['tribe'].isin(non_tribes)]

        # reduce to top k
        df = df.sort_values(by = 'std_split')\
            .head(top_k)\
            .reset_index(drop = True)
        
        if save_data:
            df.to_csv('../reports/kindred_even_color_splits.csv')
        
        return df