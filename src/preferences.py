
columns_to_drop = ['code', 'cost_change_event', 'cost_change_event_fall', 'cost_change_start', 'cost_change_start_fall',
                   'ep_next', 'ep_this', 'photo', 'special', 'squad_number', 'team_code', 'transfers_in_event',
                   'transfers_out_event', 'influence_rank_type', 'creativity_rank_type', 'threat_rank_type',
                   'ict_index_rank_type', 'corners_and_indirect_freekicks_text', 'direct_freekicks_text', 'penalties_text']

understat_columns_to_drop = ['id', 'time', 'goals', 'assists', 'yellow_cards', 'red_cards', 'position', 'team_title']

players_to_rename = {'Rúben Dias':'Rúben Santos Gato Alves Dias'}