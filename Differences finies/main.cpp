#include <iostream>
#include <fstream>
#include <math.h> // sinon il ne reconnaît pas pow(x,n)
#include <stdlib.h>

using namespace std;

int main(){

    ofstream mon_fichier("graphique.txt") ; // ouvre le nouveau fichier en Ã©criture

    cout << "Calcul numérique" << endl;
    cout << "Influence de la taille du maillage sur cylindrique" << endl;

    double R1 = 0.5; // taille du rayon
    double R2 = 0.65; // taille du rayon
    double Pi = 3.1415926;
    double dR;
    double surface_num;
    double surface_theo;
    int n ;
    double numeriq[100];
    double analytiq[100];
    double err[100];
    int j = 1;

    for (n=3 ; n<50 ; n+=1)
    {
        dR = (R2-R1)/n;
        surface_theo = Pi * (pow(R2,2)-pow(R1,2));
        surface_num = 0;

        for (int i=1 ; i <= n ; i++){
            surface_num = 2*Pi* (i*dR+R1)*dR + surface_num;
        }

        numeriq[j] = surface_num;
        analytiq[j] = surface_theo;
        err[j] = (surface_num-surface_theo)/surface_theo*100;
        mon_fichier << n << ' ' << numeriq[j] << ' ' << analytiq[j] << ' ' << err[j]  << '\n' << endl; // Ã©criture dans le fichier graphique.date
        j += 1;
    }

    mon_fichier.close() ; // fermeture du fichier Ã©criture
#ifdef _WIN32
    system("gnuplot graphique.txt"); // il faut modifier le fichier plot.gp pour changer les conditions
    system("del *.eps"); // on supprime le .eps qui est crÃ©Ã© via gnuplot
#else
    system("gnuplot plot_courbe.gp"); // il faut modifier le fichier plot.gp pour changer les conditions
    system("rm *.eps"); // on supprime le .eps qui est crÃ©Ã© via gnuplot
#endif
    return 0;
}
