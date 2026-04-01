#version 410 core

in vec2 TexCoord;
out vec4 FragColor;

uniform sampler2D screenTex;
uniform sampler2D noise;
uniform sampler2D lightTex;

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

    float noise1 = texture(noise, vec2(uv.x - time * 0.0001, uv.y - time * 0.0001)).r;
    float noise2 = texture(noise, vec2(uv.x - time * 0.00003, uv.y - time * 0.00002)).r;
    float pNoise = (noise1 + noise2) * 0.5;

    vec4 tex = texture(screenTex, TexCoord);

    vec2 scrUV = TexCoord * vec2(scrWidth, scrHeight);
    vec2 scroll = vec2(scrollX, scrollY);

    vec2 baseTile = floor(scroll / 8.0) - vec2(1.0);
    vec2 tileWS = (scroll + scrUV) / 8.0;
    vec2 tileLS = tileWS - baseTile;

    vec2 lightSize = vec2(textureSize(lightTex, 0));

    vec2 lightUV = (tileLS + vec2(0.5)) / lightSize;
    vec2 minUV = vec2(0.5) / lightSize;
    vec2 maxUV = (lightSize - vec2(0.5)) / lightSize;
    lightUV = clamp(lightUV, minUV, maxUV);

    vec4 light = texture(lightTex, lightUV - texelSize * 4.0);

    FragColor = vec4(mix(vec3(0.65, 0.6, 0.59), tex.rgb, 1.0 - pNoise * pNoise * pNoise) * light.rgb, 1.0);
}
