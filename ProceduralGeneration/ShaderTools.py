import panda3d.core as p3dc

def loadShader(source:str, directory:str="ProceduralGeneration/glsl/"):
    with open("ProceduralGeneration/glsl/classic-noise-4d.snip.glsl") as file:
        noise4d = file.read()
    with open(directory+source) as file:
        source = file.read()
    source = source.replace("__noise4d__", noise4d)
    source = source.split("__split__")
    #shader = p3dc.Shader.load(p3dc.Shader.SL_GLSL, source[0], source[1])
    shader = p3dc.Shader.make(p3dc.Shader.SL_GLSL, source[0], source[1])
    return shader
