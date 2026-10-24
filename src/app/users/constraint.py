"""
This enumeration class stores the dietary restrictions that are related to customers' health.

@author Su Chengzhang
"""
from enum import StrEnum, auto

class Allergy(StrEnum):
    NUT = auto()            #   Avoids peanuts and tree nuts (such as almonds, walnuts, and cashews) due to the risk of severe allergic reactions.
    LACTOSE = auto()        #   Limits or avoids dairy milk and products high in lactose because of a lack of the lactase enzyme.
    GLUTEN = auto()         #   Eliminates wheat, barley, rye, and products containing gluten to prevent gut inflammation.

class HealthDiet(StrEnum):
    DIABETES = auto()       #   Focuses on low-glycemic index foods like whole grains, vegetables, and legumes while limiting refined sugars.
    CHOLESTEROL = auto()    #   Lowers saturated fats, fried foods, and red meats.

class Religious(StrEnum):
    HALAL = auto()          #   Follows Islamic guidelines on permitted foods and preparation methods.
    KOSHER = auto()         #   Follows Jewish dietary laws regarding permitted animals, proper slaughter, and keeping meat and dairy separate.

class LifeStyle(StrEnum):
    VEGETARIAN = auto()     #   Excludes meat, poultry, and fish, though some variants include eggs or dairy.
    VEGAN = auto()          #   Excludes all animal-derived products, including meat, dairy, eggs, and honey.    
    
class FlavourPre(StrEnum):
    SPICY = auto()
    SUGAR = auto()
    ICE = auto()

HARD_CONSTRAINTS = (Allergy, HealthDiet, Religious, LifeStyle)
SOFT_CONSTRAINTS = (FlavourPre)

def is_hard(
    constraint: Allergy | HealthDiet | Religious | LifeStyle | FlavourPre,
) -> bool:
    return constraint.__class__ in HARD_CONSTRAINTS

def is_soft(
    constraint: Allergy | HealthDiet | Religious | LifeStyle | FlavourPre,
) -> bool:
    return constraint.__class__ in SOFT_CONSTRAINTS





    