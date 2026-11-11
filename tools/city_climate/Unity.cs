namespace UnityEngine {
  public struct Color { public float r,g,b,a; public Color(float r,float g,float b,float a=1f){this.r=r;this.g=g;this.b=b;this.a=a;}
    public static Color white=>new Color(1,1,1,1); public static Color clear=>new Color(0,0,0,0);
    public float grayscale=>0.299f*r+0.587f*g+0.114f*b;
    public static Color Lerp(Color a,Color b,float t){t=Mathf.Clamp01(t);return new Color(a.r+(b.r-a.r)*t,a.g+(b.g-a.g)*t,a.b+(b.b-a.b)*t,a.a+(b.a-a.a)*t);}
    public static bool operator==(Color x,Color y)=>x.r==y.r&&x.g==y.g&&x.b==y.b&&x.a==y.a; public static bool operator!=(Color x,Color y)=>!(x==y);
    public override bool Equals(object o)=>o is Color c&&c==this; public override int GetHashCode()=>0;
    public override string ToString()=>string.Format(System.Globalization.CultureInfo.InvariantCulture,"({0:F4}, {1:F4}, {2:F4})",r,g,b); }
  public struct Vector3 { public float x,y,z; public Vector3(float x,float y,float z){this.x=x;this.y=y;this.z=z;} }
  public static class Mathf { public static float Clamp(float v,float a,float b)=>v<a?a:v>b?b:v; public static float Clamp01(float v)=>Clamp(v,0,1);
    public static float Max(float a,float b)=>a>b?a:b; public static float Min(float a,float b)=>a<b?a:b;
    public static float GammaToLinearSpace(float c)=>c<=0.04045f?c/12.92f:(float)System.Math.Pow((c+0.055)/1.055,2.4);
    public static float LinearToGammaSpace(float c)=>c<=0.0031308f?c*12.92f:(float)(1.055*System.Math.Pow(c,1/2.4)-0.055); }
}
