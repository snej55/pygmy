#version 410 core

uniform sampler2D screenTex;
in vec2 TexCoord;
out vec4 FragColor;

void main()
{
    vec4 tex = texture(screenTex, TexCoord);
    FragColor = tex;
}
