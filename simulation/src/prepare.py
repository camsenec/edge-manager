import numpy as np
import pandas as pd
from scipy.sparse.linalg import svds
import itertools

print("Loading...")
followers_df_all = pd.read_table('../input/user_sns.txt', names=('follower', 'followee'))

id_from = 1000000
id_to = 1100000
limit = 5

df = followers_df_all[followers_df_all["followee"] > id_from]
upper = df[df["followee"] <= id_to]
lower = upper[upper["follower"] > id_from]
followers_df = lower[lower["follower"] <= id_to]

#users who belongs to a group whose size is greater than or equal to 5
followers_count_df = followers_df.groupby(['follower']).size()
followers_with_enough_followees_df = followers_count_df[ followers_count_df >= limit].reset_index()[['follower']]
selected_df =  followers_df.merge(followers_with_enough_followees_df,
               how = 'right',
               left_on = 'follower',
               right_on = 'follower')

groups = selected_df.groupby('follower')['followee'].apply(list)
groups_df = pd.DataFrame(groups).reset_index()
groups_df.to_csv("../out/tx_log.csv", index=True, header=False)

# append self
for send_from in groups.keys():
    groups[send_from].append(send_from)

# extract all possible pairs in the group
for send_from in groups.keys():
  groups[send_from] = list(itertools.permutations(groups[send_from],2))

pairs = []
for send_from in groups.keys():
    pairs.extend(groups[send_from])

sender_receiver = pd.DataFrame(pairs, columns= ["sender","receiver"]); sender_receiver["count"] = 1
pivot_table = sender_receiver.pivot_table(values="count",index='sender', columns='receiver', aggfunc = 'count').fillna(0)
pivot_matrix = pivot_table.values

# Matrix Factorization by SVD (Singular Value Decomposition)
NUMBER_OF_FACTORS_MF = int(pivot_table.shape[0] * (0.1))
U, sigma, Vt = svds(pivot_matrix, k = NUMBER_OF_FACTORS_MF)
sigma = np.diag(sigma)

predicted_ratings = np.dot(np.dot(U, sigma), Vt)
svd_preds_df = pd.DataFrame(predicted_ratings, columns = pivot_table.columns, index=pivot_table.index)

res = pd.DataFrame(columns=['related_clients'])
for client_id in svd_preds_df.keys():
    sorted_client_predictions = list(svd_preds_df[client_id].sort_values(ascending=False).keys())
    res.loc[client_id] = [sorted_client_predictions]

res.to_csv('../out/relationship.csv', header = False, index=True)
