from gideon import GideonCapture

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Gideon Screen Recording and Analysis System')
    parser.add_argument('--output', default='./temp_photo', help='Output folder for recordings')
    parser.add_argument('--fps', type=int, default=20, help='Frames per second')
    parser.add_argument('--interval', type=int, default=5, help='Deduplication interval in seconds')
    
    args = parser.parse_args()
    
    gideon = GideonCapture(
        output_folder=args.output,
        fps=args.fps,
        dedup_interval=args.interval
    )
    
    try:
        gideon.start()
        
        while True:
            question = input("\nAsk a question (or 'quit' to exit): ")
            if question.lower() == 'quit':
                break
            
            answer = gideon.query(question)
            print(f"\nAnswer: {answer}")
            
    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt")
    finally:
        gideon.stop()

if __name__ == "__main__":
    main()