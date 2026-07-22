Shader "AIEngineer/CapsulePortrait"
{
    Properties
    {
        _MainTex ("Portrait", 2D) = "white" {}
    }
    SubShader
    {
        Tags { "Queue"="Transparent" "RenderType"="Transparent" }
        Blend SrcAlpha OneMinusSrcAlpha
        ZWrite Off
        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"

            sampler2D _MainTex;
            float4 _MainTex_ST;

            struct appdata { float4 vertex : POSITION; float2 uv : TEXCOORD0; };
            struct v2f { float4 vertex : SV_POSITION; float2 uv : TEXCOORD0; float2 maskUv : TEXCOORD1; };

            v2f vert (appdata v)
            {
                v2f o;
                o.vertex = UnityObjectToClipPos(v.vertex);
                o.uv = TRANSFORM_TEX(v.uv, _MainTex);
                o.maskUv = v.uv;
                return o;
            }

            fixed4 frag (v2f i) : SV_Target
            {
                fixed4 color = tex2D(_MainTex, i.uv);
                float2 capsulePos = (i.maskUv - 0.5) * float2(1.0, 2.0);
                float2 segmentStart = float2(0.0, -0.5);
                float2 segmentEnd = float2(0.0, 0.5);
                float2 segmentVector = segmentEnd - segmentStart;
                float along = saturate(dot(capsulePos - segmentStart, segmentVector) / dot(segmentVector, segmentVector));
                float distanceToCapsule = length(capsulePos - segmentStart - segmentVector * along) - 0.5;
                color.a *= smoothstep(0.01, -0.01, distanceToCapsule);
                return color;
            }
            ENDCG
        }
    }
}
