#version 100
precision highp float;

uniform mat4 uModel;
uniform mat4 uView;
uniform mat4 uProjection;

in vec4 p3d_Vertex;
uniform mat4 p3d_ModelViewProjectionMatrix;
out vec3 pos;

void main() {
    gl_Position = uProjection * uView * uModel * p3d_ModelViewProjectionMatrix * p3d_Vertex;
    pos = (uModel * p3d_ModelViewProjectionMatrix * p3d_Vertex).xyz;
}


__split__


#version 100
precision highp float;

uniform vec3 uPosition;
uniform vec3 uColor;
uniform float uSize;
uniform float uFalloff;

out vec3 pos;

void main() {
    vec3 posn = normalize(pos);
    float d = clamp(dot(posn, normalize(uPosition)), 0.0, 1.0);
    float c = smoothstep(1.0 - uSize * 32.0, 1.0 - uSize, d);
    c += pow(d, uFalloff) * 0.5;
    vec3 color = mix(uColor, vec3(1,1,1), c);
    gl_FragColor = vec4(color, c);

}
