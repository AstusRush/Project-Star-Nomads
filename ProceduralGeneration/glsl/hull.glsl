#version 150
precision highp float;

in vec4 p3d_Vertex;
in vec2 p3d_MultiTexCoord0;
in vec4 p3d_Color;

uniform mat4 p3d_ModelViewProjectionMatrix;

out vec4 pColor;
out vec3 pos;
out vec4 Vert;
out vec2 uv;

void main() {
    Vert = p3d_Vertex;
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    pos = (p3d_ModelViewProjectionMatrix * p3d_Vertex).xyz;
    uv = p3d_MultiTexCoord0;
    pColor = p3d_Color;
}


__split__


#version 150
precision highp float;

in vec4 Vert;
in vec3 pos;
in vec2 uv;
in vec4 pColor;
uniform sampler2D p3d_Texture0;
out vec4 p3d_FragColor;

__util__

void main() {
    vec3 posn = normalize(pos);
    
    vec4 c = vec4(0.);
    
    c = texture2D(p3d_Texture0, uv)/10 + pColor;
    vec3 coords = floor(fract(abs(Vert.xyz)*2-0.00001)*10)/10;
    if(minComponent(coords)<0.1)
        c.rgb = vec3(0.0);//floor(fract(abs(Vert.xyz))*10)/10;
    
    p3d_FragColor = c;
}
