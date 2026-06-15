import random

_MESSAGES = {
    "one": [
        ["first try.", "okay.", "that was fast.", "alright then.", "one guess. cool."],
        ["two in a row.", "doing it again huh.", "back to back.", "okay that's not luck.", "twice now."],
        ["three.", "three times.", "still going.", "at this point just admit you're built different.", "three in a row."],
        ["four 1/6s in a row.", "four times.", "this is getting silly.", "four.", "okay we get it."],
        ["five.", "five in a row.", "five 1/6s. alright.", "five times now.", "five. okay."],
        ["six in a row.", "six 1/6s.", "six times.", "six.", "at this point it's just your thing."],
        ["seven.", "seven in a row.", "seven 1/6s.", "seven times.", "seven. still going."],
        ["eight.", "eight in a row.", "eight 1/6s.", "eight times.", "eight. okay."],
        ["nine.", "nine in a row.", "nine 1/6s.", "nine times.", "nine. still."],
        ["ten.", "ten in a row.", "ten 1/6s.", "ten times.", "ten. you're done. retire."],
    ],
    "six": [
        ["6/6. made it.", "last guess.", "close.", "squeaked through.", "cutting it close."],
        ["6/6 again.", "last guess again.", "two in a row.", "still doing the last guess thing.", "close twice now."],
        ["three 6/6s.", "last guess three times.", "three in a row.", "you really wait until the end huh.", "three times."],
        ["four 6/6s.", "four last guesses.", "four in a row.", "four times.", "still doing it."],
        ["five 6/6s.", "five last guesses.", "five in a row.", "five times.", "five. okay."],
        ["six 6/6s.", "six last guesses.", "six in a row.", "six times.", "it's your thing at this point."],
        ["seven 6/6s.", "seven last guesses.", "seven in a row.", "seven times.", "seven."],
        ["eight 6/6s.", "eight last guesses.", "eight in a row.", "eight times.", "eight."],
        ["nine 6/6s.", "nine last guesses.", "nine in a row.", "nine times.", "nine."],
        ["ten 6/6s.", "ten last guesses.", "ten in a row.", "ten times.", "ten. you never guess early. ever."],
    ],
    "fail": [
        ["rip.", "didn't get it.", "happens.", "the word wins.", "tough one."],
        ["two in a row.", "two fails.", "rough patch.", "back to back.", "two."],
        ["three fails.", "three in a row.", "rough.", "three.", "still going."],
        ["four fails.", "four in a row.", "four.", "rough stretch.", "still here though."],
        ["five fails.", "five in a row.", "five.", "okay.", "five. rough."],
        ["six fails.", "six in a row.", "six.", "six losses.", "still showing up though."],
        ["seven fails.", "seven in a row.", "seven.", "seven losses.", "seven. damn."],
        ["eight fails.", "eight in a row.", "eight.", "eight losses.", "eight. still here."],
        ["nine fails.", "nine in a row.", "nine.", "nine losses.", "nine. respect for still playing."],
        ["ten fails.", "ten in a row.", "ten.", "ten losses.", "ten. you're still here. that's something."],
    ],
    "hard_one": [
        ["hard mode didn't even matter lol.", "first guess. hard mode was irrelevant.", "hard mode: completely bypassed.", "the rules never even applied.", "hard mode said nothing."],
        ["twice. hard mode still irrelevant.", "two hard mode 1/6s.", "back to back. hard mode was a spectator.", "two times. hard mode didn't get a chance.", "twice now. hard mode is decorative."],
        ["three hard mode 1/6s.", "three times. hard mode is just vibes at this point.", "three. hard mode never activated.", "three in a row. hard mode is confused.", "three. the rules had nothing to enforce."],
        ["four hard mode 1/6s.", "four times. hard mode is just there for the icon.", "four. hard mode never got involved.", "four in a row. hard mode is irrelevant four times over.", "four. okay."],
        ["five hard mode 1/6s.", "five times. hard mode is a formality.", "five. hard mode never stood a chance.", "five in a row. hard mode is just decoration.", "five. hard mode didn't matter once."],
        ["six hard mode 1/6s.", "six times. hard mode is purely cosmetic.", "six. hard mode never applied.", "six in a row. hard mode is just the lock icon.", "six. okay."],
        ["seven hard mode 1/6s.", "seven times. hard mode is a myth.", "seven. hard mode never got to do anything.", "seven in a row. hard mode is just a vibe.", "seven. hard mode is irrelevant."],
        ["eight hard mode 1/6s.", "eight times. hard mode is just there.", "eight. hard mode never mattered.", "eight in a row. hard mode is decorative.", "eight. okay."],
        ["nine hard mode 1/6s.", "nine times. hard mode is a spectator sport.", "nine. hard mode never activated once.", "nine in a row. hard mode is just the lock emoji.", "nine. hard mode is irrelevant."],
        ["ten hard mode 1/6s.", "ten times. hard mode never applied. not once.", "ten. hard mode is purely aesthetic at this point.", "ten in a row. hard mode is just vibes.", "ten. the lock is decorative."],
    ],
    "hard_six": [
        ["6/6 in hard mode. that was rough to watch.", "last guess. hard mode. somehow.", "hard mode 6/6. barely.", "made it. hard mode. last guess.", "hard mode and last guess. okay."],
        ["two hard mode 6/6s.", "last guess in hard mode. twice.", "back to back. hard mode. last guess.", "two times. hard mode. last guess.", "twice. hard mode 6/6."],
        ["three hard mode 6/6s.", "three times. hard mode. last guess.", "three in a row. hard mode barely.", "three. hard mode. last guess.", "three hard mode 6/6s. rough."],
        ["four hard mode 6/6s.", "four times. hard mode. last guess.", "four in a row. hard mode barely.", "four. hard mode. last guess.", "four. okay."],
        ["five hard mode 6/6s.", "five times. hard mode. last guess.", "five in a row. hard mode barely.", "five. hard mode. last guess.", "five. still going."],
        ["six hard mode 6/6s.", "six times. hard mode. last guess.", "six in a row. hard mode barely.", "six. hard mode. last guess.", "six. it's your thing."],
        ["seven hard mode 6/6s.", "seven times. hard mode. last guess.", "seven in a row. hard mode barely.", "seven. hard mode. last guess.", "seven."],
        ["eight hard mode 6/6s.", "eight times. hard mode. last guess.", "eight in a row. hard mode barely.", "eight. hard mode. last guess.", "eight."],
        ["nine hard mode 6/6s.", "nine times. hard mode. last guess.", "nine in a row. hard mode barely.", "nine. hard mode. last guess.", "nine."],
        ["ten hard mode 6/6s.", "ten times. hard mode. last guess.", "ten in a row. hard mode barely.", "ten. hard mode. last guess.", "ten. you always make it on the last guess in hard mode. always."],
    ],
    "hard_win": [
        ["got it. in hard mode.", "win. hard mode.", "hard mode win.", "got it with the extra rules.", "hard mode. still got it."],
        ["two hard mode wins.", "two in a row. hard mode.", "back to back hard mode wins.", "two wins. hard mode both times.", "twice. hard mode."],
        ["three hard mode wins.", "three in a row. hard mode.", "three wins with the rules on.", "three. hard mode.", "three in a row. still winning."],
        ["four hard mode wins.", "four in a row. hard mode.", "four wins. hard mode.", "four. hard mode.", "four in a row. okay."],
        ["five hard mode wins.", "five in a row. hard mode.", "five wins. hard mode.", "five. hard mode.", "five in a row. still going."],
        ["six hard mode wins.", "six in a row. hard mode.", "six wins. hard mode.", "six. hard mode.", "six in a row. it's your thing."],
        ["seven hard mode wins.", "seven in a row. hard mode.", "seven wins. hard mode.", "seven. hard mode.", "seven in a row."],
        ["eight hard mode wins.", "eight in a row. hard mode.", "eight wins. hard mode.", "eight. hard mode.", "eight in a row."],
        ["nine hard mode wins.", "nine in a row. hard mode.", "nine wins. hard mode.", "nine. hard mode.", "nine in a row."],
        ["ten hard mode wins.", "ten in a row. hard mode.", "ten wins. hard mode.", "ten. hard mode.", "ten in a row. hard mode every time."],
    ],
    "hard_fail": [
        ["rip. in hard mode.", "didn't get it. hard mode.", "hard mode fail.", "the word wins. hard mode.", "tough one. hard mode didn't help."],
        ["two hard mode fails.", "two in a row. hard mode.", "back to back. hard mode.", "two fails. hard mode both times.", "twice. hard mode."],
        ["three hard mode fails.", "three in a row. hard mode.", "three fails. hard mode.", "three. hard mode.", "three in a row. rough."],
        ["four hard mode fails.", "four in a row. hard mode.", "four fails. hard mode.", "four. hard mode.", "four in a row. still here."],
        ["five hard mode fails.", "five in a row. hard mode.", "five fails. hard mode.", "five. hard mode.", "five in a row. okay."],
        ["six hard mode fails.", "six in a row. hard mode.", "six fails. hard mode.", "six. hard mode.", "six in a row. still showing up."],
        ["seven hard mode fails.", "seven in a row. hard mode.", "seven fails. hard mode.", "seven. hard mode.", "seven in a row. damn."],
        ["eight hard mode fails.", "eight in a row. hard mode.", "eight fails. hard mode.", "eight. hard mode.", "eight in a row. still here."],
        ["nine hard mode fails.", "nine in a row. hard mode.", "nine fails. hard mode.", "nine. hard mode.", "nine in a row. respect."],
        ["ten hard mode fails.", "ten in a row. hard mode.", "ten fails. hard mode.", "ten. hard mode.", "ten in a row. you're still playing hard mode. that's something."],
    ],
}


def get_reaction_message(rtype: str, streak: int):
    pool = _MESSAGES.get(rtype)
    if not pool:
        return None
    tier = min(streak - 1, len(pool) - 1)
    return random.choice(pool[tier])
