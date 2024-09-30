import discord
from secret import USE_TEST_BOT

# Guild ID's. // Jack
GUILD_ID = 864441968776052747 if USE_TEST_BOT else 288446755219963914
GUILD = discord.Object(id=GUILD_ID)

# Channel ID's. // Jack
COMMENDATIONS_CHANNEL_ID = 1274979300386275328 if USE_TEST_BOT else 1109263109526396938
REPORT_LOG_CHANNEL_ID = 866938361628852224 if USE_TEST_BOT else 889752071815974952
UNIT_STAFF_CHANNEL_ID = 864442610613485590 if USE_TEST_BOT else 740368938239524995

# Role ID's. // Jack
UNIT_STAFF_ROLE_ID = 864443672032706560 if USE_TEST_BOT else 655465074982518805
CURATOR_ROLE_ID = 977543359432380456 if USE_TEST_BOT else 392773303770677248
ZEUS_ROLE_ID = 977543532904583199 if USE_TEST_BOT else 796178478142849048
ZEUSINTRAINING_ROLE_ID = 1133852373836640306 if USE_TEST_BOT else 988950379330941050

# Information for commend_candidate_tracking.py. // Jack
OPERATION_KEYWORD = "has attended an operation"
TOTAL_OPERATIONS = 3
