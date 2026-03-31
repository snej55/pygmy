#version 410 core

in vec2 TexCoord;
out vec4 FragColor;

uniform sampler2D screenTex;
uniform sampler2D noise;
uniform float time;
uniform float scrWidth;
uniform float scrHeight;
uniform float scrollX;
uniform float scrollY;

void main()
{
    vec2 uv = TexCoord * 0.2;
    uv.x *= scrWidth / scrHeight * 0.5;
    vec2 texelSize = vec2(1.0 / scrWidth, 1.0 / scrHeight);
    uv.x += scrollX * texelSize.x * 0.1;
    uv.y += scrollY * texelSize.y * 0.1;
    vec2 noise1uv = vec2(uv.x - time * 0.0001, uv.y - time * 0.0001);
    // noise1uv.x = floor(noise1uv.x / texelSize.x) * texelSize.x;
    // noise1uv.y = floor(noise1uv.y / texelSize.y) * texelSize.y;
    float noise1 = texture(noise, noise1uv).r;
    vec2 noise2uv = vec2(uv.x - time * 0.00003, uv.y - time * 0.00002);
    // noise2uv.x = floor(noise2uv.x / texelSize.x) * texelSize.x;
    // noise2uv.y = floor(noise2uv.y / texelSize.y) * texelSize.y;
    float noise2 = texture(noise, noise2uv).r;
    float pNoise = (noise1 + noise2) * 0.5;
    vec4 tex = texture(screenTex, TexCoord);
    float gray = min(1.0, (tex.r + tex.g + tex.b) * 0.333);
    // if (gray > 0.001)
    // pNoise = 0.0;
    FragColor = vec4(mix(vec3(0.65, 0.6, 0.59), tex.rgb, 1.0 - pNoise * pNoise * pNoise), 1.0);
}
