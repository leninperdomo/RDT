# RDT
Reliable Data Transfer 3.0 Implementation Over TCP

The goal of this Project was to transfer the first 200 bytes of data of a text file over a network using RDT 3.0. With this implementation, a sender sends data to
a receiver through an intermediary server. The sender sends 20 bytes of data at a time. By using acknowledgement numbers, sequence numbers, and checksum values,
The sender and receiver stay synchronized throughout the entire data transfer process. This means that sender and receiver can handle corrupt, delayed, and lost packets
while assuring that all the data is transferred without errors.

This project was implemented entirely using Python 3.0.
