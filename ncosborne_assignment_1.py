
#ncosborne
#
#SUBMISSION AND EXECUTION
#Keep all five function names and parameter lists unchanged. Return results;
#do not replace returns with print statements. Do not use input() or run tests
#at module level. Put any local test calls under if __name__ == "__main__":.
#No imports are needed or permitted in the submitted file for this exercise.
#Enter your name and HawkID below. Save as hawkid_assignment_1.py, upload that
#file to ICON, and commit and push the identical file to your GitHub repository.
#ICON is the graded submission. Identity mistakes will be flagged for correction,
#not assigned an automatic zero. The GitHub copy will be checked.

#VALID INPUTS AND EDGE CASES
#CSV input has no header, no blank lines, and exactly four comma-separated fields
#per row. Fields contain no embedded commas or quotes and no surrounding spaces.
#The last line may or may not have a newline. An empty file is valid.

#Names are nonempty strings. 
    #Types are exactly Water, Fire, Electric, Grass, or Ground. 
    #Health and base damage are positive finite numbers. Convert both to
#float. No malformed-input handling is required. 
#first2attack is always 1 or 2.
#Never change input participant lists, including their health. 
    #Every match starts at the original full health. 
    #One attack counts as one round; stop immediately when either health becomes <= 0 (including exactly zero). Do not round damage
#or health.
#tournament([]) returns []; a one-participant tournament returns [0].


def hawkid():
    return(["Nina Osborne", "ncosborne"])

def import_data(filename):
    participants = [] # 1. Create a list to store all pokemons (MAIN)
    with open(filename) as source:  # (1) Use open, a for loop over lines, strip(), and split(",").  # 2. Open the CSV file with given `filename` 
        for line in source: 
            fields = line.strip().split(',')     #       3.1. Since each line ends with new line, do not forget to strip it
            pokemon = [fields[0], fields[1], float(fields[2]), float(fields[3])]   # (2) Use float() for both numbers and append each row to a nested list.
            participants.append(pokemon)  #       3.3. Add -i.e., append- this POKEMON list object to MAIN list object.
        return participants

    # Do not use csv, pandas, numpy, or any other imported helper.
    #    return the MAIN list.

def attack_multiplier(attacker_type, defender_type):
    if attacker_type == 'Water' and defender_type == 'Fire':   # 1. If Attacker is Water and Defender is Fire, return 2.5
        return 2.5
    elif attacker_type == 'Electric' and defender_type == 'Water':    # 2. Else if Attacker is Electric and Defender is Water, return 1.3
        return 1.3
    elif attacker_type == 'Ground' and defender_type == 'Electric':  # 3. Else if Attacker is Ground and Defender is Electric, return 2.0
        return 2.0
    elif attacker_type == 'Fire' and defender_type == 'Grass':     # 4. Else if Attacker is Fire and Defender is Grass, return 3.0
        return 3.0
    elif attacker_type == 'Grass' and defender_type == 'Water':   # 5. Else if Attacker is Grass and Defender is Water, return 1.5
        return 1.5
    else:
        return 1.0     # 6. Else, return 1.0
   

def fight(participant1, participant2, first2attack): #do not modify either input list
    rounds = 0 # 1. Initialize rounds variable:
    variable1 = participant1[2]  # 2. Store the initial health of both participants in two variables.
    variable2 = participant2[2]  # 2. Store the initial health of both participants in two variables.
    while variable1 > 0 and variable2 > 0:  # 3. While both of the healths (use variable1 and variable2) are greater than 0:
        if first2attack == 1:   #       3.1. If first to attack is 1:
            multiplier = attack_multiplier(participant1[1], participant2[1]) #(Hint: You should call attack_multiplier function)
            damage = multiplier * participant1[3]   #           3.1.2. Calculate new attack damage by multiplying the attack multiplier with base damage
            variable2 = variable2 - damage    #           3.1.3. Subtract new attack damage from the second participant's health
        else:  #       3.2. Else if first to attack is 2 (or Else):
            multiplier = attack_multiplier(participant2[1], participant1[1]) #(Hint: You should call attack_multiplier function)
            damage = multiplier * participant2[3] #3.2.2. Calculate new attack damage by multiplying the attack multiplier with base damage
            variable1 = variable1 - damage #           3.2.3. Subtract new attack damage from the first participant's health
        rounds = rounds + 1  #       3.3. Increment the rounds variable by one.
        if first2attack == 1: #       3.4. Toggle first2attack variable. (If it is 1, make it 2. 
            first2attack = 2
        elif first2attack == 2: 
            first2attack = 1 
    if variable1 > 0:    # 4. If variable1 is greater than 0, then winner is 1. However, if variable 2 is greater than 0,
        winner = 1
    else:
        winner = 2 #winner 2
    return [winner, rounds]


def tournament(participants):
    wins = [] #initialize list of wins
    for i in range (len(participants)): #what pokemon is up
        wins.append(0) #each participant from list length gets 0 to start. once per pokemon
    for i in range (len(participants)): 
        firstpokemon = participants[i]
        for j in range(i + 1, len(participants)): #for remaining participants (1 more than first)
            secondpokemon = participants[j]
            home_result = fight(firstpokemon, secondpokemon, 1) #play home game, firstpokemon attacks first
            home_winner = home_result[0]
            away_result = fight(firstpokemon, secondpokemon, 2)  #play away game, secondpokemon attacks first
            away_winner = away_result[0]
        if home_winner == 1: #first pokemon won, use i inedx
            wins[i] = wins[i] + 1
        elif home_winner == 2: #second pokemon won, use j index
            wins[j] = wins[j] + 1
        if away_winner == 1: # 2.1.3 Check result of the away game
            wins[i] = wins[i] + 1
        elif away_winner == 2:
            wins[j] = wins[j] +1
    return wins

    #       2.1. For each remaining participant in the list: (starting from (the index of first participant) + 1, until the last one)
    #           2.1.1. Play a home game. Call fight function and pass 1 as the third parameter (we defined fight earlier with 3 parameters)
    #           2.1.2. Play an away game. Call fight function and pass 2 as the third parameter #so first to attack is 2, which means that it will be coming from the "opposing" team
  