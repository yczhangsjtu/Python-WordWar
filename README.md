Python-WordWar
==============

A python game aimed at helping Chinese users to memorize English words

There are more than a hundred cities on the map, and more than a dozen countries
identified by different colors.

You start by selecting your color of country and fight with others until you
conquer all the cities.

Originally each country owns eight cities.

================================================================================
Click on your city and you can do the following operations:

1. Move your troop(Set Out)

Select some words and set out, click the target city. If the target is your own,
you just move your troop. And if the target is an enemy city, you are picking up
a fight.

2. Recruit some words.

When initializing the game reads a large database of words (currently it is the
GRE word set, and there are about 6000 of them).

If some words in the database are not in any of the cities (dead in battles),
you can recruit them. The number of such words are shown at the right-bottom.

Input the right word and press Enter, you'll get the word into your city. If you
made a mistake, the recruit panel will be gone and there is chance that the
words are recruited by other contries.

================================================================================

On the screne are:

1. The information of all the countries. Color name followed by total number of
words and number of cities

2. The number of unrecruited words at the right-bottom.

3. City information when you put your mouse on some city

================================================================================

On the battle field:

When you are attacking someone else or are being attacked, you'll be put into
the battle field. The movements of all soldiers are all automatic (controlled by
simple AI that all the soldiers are moving towards their nearest enemies).

When your soldier encounter an enemy, the enemy's words will be provided and you
are expected to select the correct Chinese meaning given the word, or the
correct word given the Chinese. A selection among four.

Your soldier dies when you make a single mistake.

================================================================================

Other files:

new.txt and all save files are in the same format.

new.txt is used to start a new game. Feel free to change it. It is just like a
default save file.

Each line is in the form: cityNumber.attribute = value

The statements of a city of the country denoted by red is like:

city3.x = 123
city3.y = 456
city3.color = 0
city3.addWord = hello
city3.addWord = world
city3.addWord = word
city3.addWord = war

"addWord" is used to add a word to the city.

If this city belongs to the player, then there will be

city3.color = yourColor

And all the unrecruited words are

deadWords0.addWord = dead

The 0 here is for unification.

The color is indexed by number, and the correspondence can be found at the most
top of the python program.

================================================================================

Final word:

The game is silent. I also implemented another version with pyglet which
supports audio, but unfortunately the performance is untolerably bad. So I have
to give up.
