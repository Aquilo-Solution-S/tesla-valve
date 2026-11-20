-- expect: Effect does IO
abbrev Effect := IO

def announce : Effect Unit := IO.println "shipped"
