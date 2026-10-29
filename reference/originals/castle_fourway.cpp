#include <cstdint>
#include <cmath>
#include <algorithm>

extern "C" void evaluate(const int16_t* actions, int count, const int8_t* table, int groups, int scenarios, double* out) {
    const int pay[4][4]={{108,78,60,45},{48,36,24,0},{24,12,0,0},{0,0,0,0}};
    const int per=groups/scenarios;
    #pragma omp parallel for schedule(static)
    for(int a=0;a<count;a++) {
        const int8_t *p[5];
        for(int j=0;j<5;j++) p[j]=table+((j*101+actions[a*5+j])*groups)*4;
        for(int sc=0;sc<scenarios;sc++) {
            int total=0;
            for(int r=sc*per;r<(sc+1)*per;r++) {
                int own=0,s1=0,s2=0,s3=0;
                int offset=r*4;
                for(int j=0;j<5;j++) {
                    own+=p[j][offset];s1+=p[j][offset+1];s2+=p[j][offset+2];s3+=p[j][offset+3];
                }
                int greater=(s1>own)+(s2>own)+(s3>own);
                int equal=(s1==own)+(s2==own)+(s3==own);
                total+=pay[greater][equal];
            }
            out[a*scenarios+sc]=total/(12.0*per);
        }
    }
}
