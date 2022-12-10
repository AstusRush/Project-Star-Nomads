#CRITICAL: Write a debug tab to properly test the game
#           Here is already a first function that can be used:
def spawnAsteroidAtSelectedHex():
    from BaseClasses import Environment, get
    currentHex = get.hexGrid().SelectedHex
    #TODO: Ensure that the hex is empty before spawning anything!
    combat = get.engine().CurrentlyInBattle
    object = Environment.Asteroid()
    if not combat: objectGroup = Environment.EnvironmentalObjectGroup_Campaign()
    else: objectGroup = Environment.EnvironmentalObjectGroup_Battle()
    objectGroup.Name = object.Name
    objectGroup.addShip(object)
    objectGroup.moveToHex(currentHex, False)
