

const float pi = 3.14159265359;


float maxComponent(vec2 v) { return max(v.x, v.y); }
float maxComponent(vec3 v) { return max(max(v.x, v.y), v.z); }
float maxComponent(vec4 v) { return max(max(max(v.x, v.y), v.z), v.w); }
float minComponent(vec2 v) { return min(v.x, v.y); }
float minComponent(vec3 v) { return min(min(v.x, v.y), v.z); }
float minComponent(vec4 v) { return min(min(min(v.x, v.y), v.z), v.w); }

uint getLastDigits(uint i, int d){
    int dp = 1;
    for(int ii = 0; ii<d; ii++) dp /= 10;
    float r = fract(float(i)/dp)*dp;
    return uint(r);
}

uint getLastBits(uint i, int d){
    uint mask = (uint(1) << uint(d)) - uint(1);
    uint little = i & mask;
    return little;
}

vec3 cartesianToSpherical(vec3 cartesianCoords) {
    float r = length(cartesianCoords);
    float phi = acos(cartesianCoords.z / r);
    float theta = atan(cartesianCoords.y, cartesianCoords.x);
    return vec3(theta, phi, r);
}

vec3 sphericalToCartesian(float theta, float phi, float r) {
    float x = r * sin(phi) * cos(theta);
    float y = r * sin(phi) * sin(theta);
    float z = r * cos(phi);
    return vec3(x, y, z);
}

vec3 sphericalToCartesian(vec3 v) {
    return sphericalToCartesian(v.x, v.y, v.z);
}

vec3 sfract(vec3 v, float mult) {
    v = cartesianToSpherical(v);
    v *= mult;
    v = fract(v);
    v /= mult;
    v = sphericalToCartesian(v);
    return v;
}

vec3 sfract(vec3 v) {
    return sfract(v, 1.0);
}

vec3 equalizeLength(vec3 v, vec3 w){
    v = cartesianToSpherical(v);
    w = cartesianToSpherical(w);
    v.x = w.x;
    return sphericalToCartesian(v);
}

vec3 hash3(vec3 p) {
    p=vec3( dot(p, vec3(127.1, 311.7, 74.7)),
            dot(p, vec3(269.5, 183.3, 246.1)),
            dot(p, vec3(113.5, 271.9, 124.6)));
    return -1.0 + 2.0 * fract(sin(p) * 43758.5453123);
}

vec2 hash2(vec2 p) {
    p=vec2( dot(p, vec2(127.1, 311.7)),
            dot(p, vec2(269.5, 183.3)));
    return -1.0 + 2.0 * fract(sin(p) * 43758.5453123);
}

float hash3f(vec3 co){
    return -1.0 + 2.0 * fract(sin(dot(co.xyz, vec3(12.9898, 78.233, 54.53))) * 43758.5453);
}

float hash2f(vec2 p) {
    return -1.0 + 2.0 * fract(sin(dot(p.xy, vec2(311.7, 74.7))) * 43758.5453123);
}

vec3 randPosS(vec2 p, vec3 p3, float l, int seed){
    vec3 r;
    
    // Generate a random distance between minDistance and maxDistance
    float dist = l;//(hash3f(p3)+1)/2;
    
    // Generate a random azimuthal angle theta between 0 and 2*pi
    float theta = (hash3f(p3+seed)+1) * pi;
    
    // Generate a uniform random value for cos(phi) between -1 and 1
    float cos_phi = hash3f(p3+seed*13.);
    
    // Calculate the polar angle phi from cos_phi
    float phi = acos(cos_phi);
    
    //// Convert spherical coordinates to Cartesian coordinates
    //r.x = dist * sin(phi) * cos(theta);
    //r.y = dist * sin(phi) * sin(theta);
    //r.z = dist * cos(phi);
    return vec3(theta, phi, dist);
}

vec3 randPosS(vec2 p, vec3 p3, float l){
    return randPosS(p, p3, l, 42);
}

vec3 randPosS(vec2 p, vec3 p3){
    return randPosS(p, p3, 1.0);
}

vec3 randPos(vec2 p, vec3 p3, float l, int seed){
    vec3 r = randPosS(p, p3, l, seed);
    return sphericalToCartesian(r);
}

vec3 randPos(vec2 p, vec3 p3, float l){
    return randPos(p, p3, l, 42);
}

vec3 randPos(vec2 p, vec3 p3){
    return randPos(p, p3, 1.0);
}
