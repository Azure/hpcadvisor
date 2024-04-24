#include "mpi.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define MASTER 0
#define FROM_MASTER 1
#define FROM_WORKER 2

// this code is for square matrix
// Usage: mpirun -np <nprocs> <matrix size> [<interactions>] [v]
// for each interaction, matrix are allocated, generated, and computed

void print_matrix(double *matrix, int rows, int cols, char *header) {

  printf("****************************************************** %s", header);
  for (int i = 0; i < rows; i++) {
    printf("\n");
    for (int j = 0; j < cols; j++)
      printf("%6.1f ", matrix[i * rows + j]);
  }
  printf("\n******************************************************\n", header);
  printf("\n");
}

double *rand_matrix(int nrows, int ncols) {

  double *matrix;

  matrix = (double *)malloc(nrows * ncols * sizeof(double));

  for (int i = 0; i < nrows; i++)
    for (int j = 0; j < ncols; j++)
      // matrix[i*nrows+j] = i + j;
      matrix[i * nrows + j] = rand() % 10;

  return matrix;
}

void matrix_multiplication(double *a, double *b, double *c, int matrix_size,
                           int rows) {

  for (int k = 0; k < matrix_size; k++)
    for (int i = 0; i < rows; i++) {
      for (int j = 0; j < matrix_size; j++)
        c[i * matrix_size + k] =
            c[i * matrix_size + k] +
            a[i * matrix_size + j] * b[j * matrix_size + k];
    }
}

void show_usage(char *program) {

  printf("Usage: %s <matrix size> [<interactions>] [v]\n", program);
  printf("v: verbose\n");
}

char is_integer(const char *str) {
  int num;
  return sscanf(str, "%d", &num) == 1;
}

void handle_arguments(int argc, char *argv[], int *matrix_size, int *verbose,
                      int *num_interactions, int *numworkers, int numtasks,
                      int taskid) {

  int rc;

  if (argc < 2) {
    if (taskid == MASTER)
      show_usage(argv[0]);
    MPI_Abort(MPI_COMM_WORLD, rc);
    exit(1);
  }

  if (numtasks < 2) {
    printf("Require at least two MPI tasks. Quitting...\n");
    MPI_Abort(MPI_COMM_WORLD, rc);
    exit(1);
  }
  *numworkers = numtasks - 1;

  if (argc > 3 && !strcmp(argv[3], "v")) {
    *verbose = 1;
  }

  if (argc > 2) {
    if (is_integer(argv[2]))
      *num_interactions = atoi(argv[2]);
    else if (!strcmp(argv[2], "v"))
      *verbose = 1;
  }

  if (!is_integer(argv[1])) {
    if (taskid == MASTER) {
      show_usage(argv[0]);
      printf("matrix size should be an number\n");
    }
    MPI_Abort(MPI_COMM_WORLD, rc);
    exit(1);
  }
  *matrix_size = atoi(argv[1]);
  if (taskid == MASTER)
    printf("matrix size= %d\n", *matrix_size);
}

int main(int argc, char *argv[]) {
  int numtasks, taskid, numworkers, source, dest, mtype;
  int rows, averow, extra, offset, i, j, k, rc;
  double *c = NULL;
  double *a = NULL;
  double *b = NULL;
  double startwtime, endwtime, beginwtime, totalstartwtime, totalendwtime;
  int matrix_size = 0;
  int verbose = 0;
  int num_interactions = 1;
  MPI_Status status;

  MPI_Init(&argc, &argv);

  MPI_Comm_rank(MPI_COMM_WORLD, &taskid);
  MPI_Comm_size(MPI_COMM_WORLD, &numtasks);

  handle_arguments(argc, argv, &matrix_size, &verbose, &num_interactions,
                   &numworkers, numtasks, taskid);

  if (taskid == MASTER) {

    if (verbose)
      printf("verbose mode active!\n");

    totalstartwtime = MPI_Wtime();
    for (int inter = 0; inter < num_interactions; inter++) {
      c = (double *)malloc(matrix_size * matrix_size * sizeof(double));
      a = rand_matrix(matrix_size, matrix_size);
      b = rand_matrix(matrix_size, matrix_size);
      startwtime = MPI_Wtime();
      printf("starting interaction %d wall clock time = %f\n", inter,
             startwtime);

      if (verbose) {
        printf("mpi_mm has started with %d tasks.\n", numtasks);
        printf("Initializing arrays...\n");
        print_matrix(a, matrix_size, matrix_size, "Matrix A");
      }

      averow = matrix_size / numworkers;
      extra = matrix_size % numworkers;
      offset = 0;
      mtype = FROM_MASTER;
      for (dest = 1; dest <= numworkers; dest++) {
        rows = (dest <= extra) ? averow + 1 : averow;
        MPI_Send(&offset, 1, MPI_INT, dest, mtype, MPI_COMM_WORLD);
        MPI_Send(&rows, 1, MPI_INT, dest, mtype, MPI_COMM_WORLD);
        MPI_Send(a + offset * matrix_size, rows * matrix_size, MPI_DOUBLE, dest,
                 mtype, MPI_COMM_WORLD);
        MPI_Send(b, matrix_size * matrix_size, MPI_DOUBLE, dest, mtype,
                 MPI_COMM_WORLD);

        offset = offset + rows;
      }

      mtype = FROM_WORKER;
      for (i = 1; i <= numworkers; i++) {
        source = i;
        MPI_Recv(&offset, 1, MPI_INT, source, mtype, MPI_COMM_WORLD, &status);
        MPI_Recv(&rows, 1, MPI_INT, source, mtype, MPI_COMM_WORLD, &status);
        MPI_Recv(c + offset * matrix_size, rows * matrix_size, MPI_DOUBLE,
                 source, mtype, MPI_COMM_WORLD, &status);
      }
      if (verbose)
        print_matrix(c, matrix_size, matrix_size, "Final Matrix C");

      endwtime = MPI_Wtime();
      printf("interaction %d wall clock time = %f\n", inter,
             endwtime - startwtime);
      fflush(stdout);
    }
    totalendwtime = MPI_Wtime();
    printf("concluded all %d total wall clock time = %f\n", num_interactions,
           totalendwtime - totalstartwtime);
    fflush(stdout);
  }

  if (taskid > MASTER) {

    for (int inter = 0; inter < num_interactions; inter++) {
      b = (double *)malloc(matrix_size * matrix_size * sizeof(double));
      a = (double *)malloc(matrix_size * matrix_size * sizeof(double));
      c = (double *)calloc(matrix_size * matrix_size, sizeof(double));

      mtype = FROM_MASTER;
      MPI_Recv(&offset, 1, MPI_INT, MASTER, mtype, MPI_COMM_WORLD, &status);
      MPI_Recv(&rows, 1, MPI_INT, MASTER, mtype, MPI_COMM_WORLD, &status);
      MPI_Recv(a, rows * matrix_size, MPI_DOUBLE, MASTER, mtype, MPI_COMM_WORLD,
               &status);
      MPI_Recv(b, matrix_size * matrix_size, MPI_DOUBLE, MASTER, mtype,
               MPI_COMM_WORLD, &status);

      matrix_multiplication(a, b, c, matrix_size, rows);

      mtype = FROM_WORKER;
      MPI_Send(&offset, 1, MPI_INT, MASTER, mtype, MPI_COMM_WORLD);
      MPI_Send(&rows, 1, MPI_INT, MASTER, mtype, MPI_COMM_WORLD);
      MPI_Send(c, rows * matrix_size, MPI_DOUBLE, MASTER, mtype,
               MPI_COMM_WORLD);
    }
  }
  MPI_Finalize();
}
