#version 410 core

in vec2 TexCoord;
out vec4 FragColor;

uniform sampler2D screenTex;
uniform sampler2D noise;
uniform sampler2D lightTex;
uniform sampler2D waterTex;
uniform sampler2D uiTex;

uniform float time;
uniform float scrWidth;
uniform float scrHeight;
uniform float scrollX;
uniform float scrollY;
uniform vec2 shockwave;
uniform float shockwaveTime;
uniform vec3 shockParams = vec3(10.0, 0.8, 0.1);

uniform float distortion = 5.0;
uniform float fogStrength = 0.2;
uniform float screenShake = 0.0;

void main()
{
    vec4 ui = texture(uiTex, TexCoord);
    if (ui.r + ui.b + ui.g > 0.0)
    {
        FragColor = ui;
        return;
    }
    vec2 texelSize = vec2(1.0 / scrWidth, 1.0 / scrHeight);
    vec2 coords = TexCoord;
    if (screenShake > 0.01)
    {
        coords -= 0.5;
        float s = sin(screenShake);
        float c = cos(screenShake);
        coords = mat2(c, -s, s, c) * coords;
        coords += 0.5;
    }
    vec3 water = texture(waterTex, TexCoord).rgb;
    if (water.r + water.g + water.b > 0.0)
    {
        vec2 noiseUV =
            vec2(TexCoord.x - time * 0.001 + scrollX * texelSize.x, TexCoord.y - time * 0.001 + scrollY * texelSize.y);
        float n = texture(noise, noiseUV).r;
        coords += (n * distortion - distortion * 0.5) * texelSize;
        vec3 modSample = texture(waterTex, coords).rgb;
        if (!(modSample.r + modSample.g + modSample.b > 0.0))
        {
            coords = TexCoord;
        }
    }

    float aspectR = scrWidth / scrHeight;

    vec2 corrUV = vec2(coords.x * aspectR, coords.y);
    vec2 coorCenter = vec2(shockwave.x * aspectR, shockwave.y);
    float dist = distance(corrUV, coorCenter);
    if ((dist <= (shockwaveTime + shockParams.z)) && (dist >= (shockwaveTime - shockParams.z)))
    {
        float diff = (dist - shockwaveTime);
        float powDiff = 1.0 - pow(abs(diff * shockParams.x), shockParams.y);
        float diffTime = diff * powDiff;
        vec2 diffUV = normalize(corrUV - coorCenter);

        coords.x += (diffUV.x * diffTime) / aspectR;
        coords.y += (diffUV.y * diffTime);
    }

    vec2 uv = coords;
    uv.x += scrollX * texelSize.x;
    uv.y += scrollY * texelSize.y;
    uv *= 0.2;
    uv.x *= scrWidth / scrHeight * 0.5;

    float noise1 = texture(noise, vec2(uv.x - time * 0.0001, uv.y - time * 0.0001)).r;
    float noise2 = texture(noise, vec2(uv.x - time * 0.00003, uv.y - time * 0.00002)).r;
    float pNoise = (noise1 + noise2) * 0.5;

    vec4 tex = texture(screenTex, coords);
    float grey = (tex.r + tex.g + tex.b) * 0.3333;

    vec2 scrUV = coords * vec2(scrWidth, scrHeight);
    vec2 scroll = vec2(scrollX, scrollY);

    vec2 baseTile = floor(scroll / 8.0) - vec2(1.0);
    vec2 tileWS = (scroll + scrUV) / 8.0;
    vec2 tileLS = tileWS - baseTile;

    vec2 lightSize = vec2(textureSize(lightTex, 0));

    vec2 lightUV = (tileLS + vec2(0.5)) / lightSize;
    vec2 minUV = vec2(0.5) / lightSize;
    vec2 maxUV = (lightSize - vec2(0.5)) / lightSize;
    lightUV = clamp(lightUV, minUV, maxUV);

    vec3 light;
    if (grey > 0.0)
    {
        light = texture(lightTex, lightUV - texelSize * 4.0).rgb;
    }
    else
    {
        light = vec3(1.0);
    }

    vec3 diffuse = mix(vec3(0.65, 0.6, 0.59), tex.rgb * light, 1.0 - pow(pNoise + fogStrength - grey * light.r, 6.0));
    FragColor = vec4(diffuse + water * 0.6, 1.0);
}
